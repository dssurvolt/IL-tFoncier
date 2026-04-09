from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notary, TransactionFolio
from land_registry.models import Property
from django.contrib import messages
from .utils import notify_transaction_update
from django.utils import timezone
from functools import wraps

from identity.decorators import notary_required

@login_required
def web_choose_notary(request, property_id):
    """Étape 1 : L'acheteur choisit un notaire certifié."""
    prop = get_object_or_404(Property, id=property_id)
    
    # Sécurité : Un compte Notaire ne peut pas être un client (acheteur/vendeur)
    from identity.models import User
    if request.user.role == User.Role.NOTARY:
        messages.error(request, "🛡️ Action impossible : un compte Notaire ne peut pas être client (acheteur/vendeur). Veuillez utiliser un compte Standard pour vos transactions personnelles.")
        return redirect('web_property_detail', pk=property_id)

    # Sécurité : On ne peut pas acheter son propre terrain
    if prop.owner_wallet == request.user:
        messages.error(request, "Vous ne pouvez pas initier une transaction sur votre propre propriété.")
        return redirect('web_property_detail', pk=property_id)

    # Vérifier s'il y a déjà une transaction ACTIVE par QUELQU'UN D'AUTRE
    active_folio = TransactionFolio.objects.filter(
        property=prop,
        status__in=[
            TransactionFolio.Step.STEP1_NOTARY_SELECTED,
            TransactionFolio.Step.STEP2_ID_VERIFIED,
            TransactionFolio.Step.STEP3_DEED_SIGNED,
            TransactionFolio.Step.STEP4_ANDF_DEPOSITED,
            TransactionFolio.Step.STEP5_TITLE_MODIFIED
        ]
    ).first()

    if active_folio:
        if active_folio.buyer == request.user:
            return redirect('web_transaction_status', folio_id=active_folio.id)
        else:
            messages.warning(request, "🛡️ Cette propriété est déjà en cours de transaction avec un autre acheteur.")
            return redirect('web_property_detail', pk=property_id)

    notaries = Notary.objects.filter(is_verified=True).order_by('avg_processing_time_days')
    return render(request, 'notaries/choose_notary.html', {
        'property': prop,
        'notaries': notaries
    })

@login_required
def web_start_transaction(request, property_id, notary_id):
    """Initialise le Folio de Transaction (Chaîne de valeur)."""
    prop = get_object_or_404(Property, id=property_id)
    notary = get_object_or_404(Notary, id=notary_id)
    
    # Sécurité : Un compte Notaire ne peut pas être un client (acheteur/vendeur)
    from identity.models import User
    if request.user.role == User.Role.NOTARY:
        messages.error(request, "🛡️ Action impossible : un compte Notaire ne peut pas être client (acheteur/vendeur). Veuillez utiliser un compte Standard.")
        return redirect('web_property_detail', pk=property_id)

    # Sécurité : On ne peut pas acheter son propre terrain
    if prop.owner_wallet == request.user:
        messages.error(request, "🛡️ Action impossible : vous êtes déjà le propriétaire de cette parcelle.")
        return redirect('web_property_detail', pk=property_id)
        
    # Vérifier s'il n'y a pas déjà une transaction en cours (N'importe quel acheteur)
    active_folio = TransactionFolio.objects.filter(
        property=prop, 
        status__in=[
            TransactionFolio.Step.STEP1_NOTARY_SELECTED, 
            TransactionFolio.Step.STEP2_ID_VERIFIED, 
            TransactionFolio.Step.STEP3_DEED_SIGNED, 
            TransactionFolio.Step.STEP4_ANDF_DEPOSITED, 
            TransactionFolio.Step.STEP5_TITLE_MODIFIED
        ]
    ).first()
    
    if active_folio:
        if active_folio.buyer == request.user:
            return redirect('web_transaction_status', folio_id=active_folio.id)
        else:
            messages.error(request, "🛡️ Transaction impossible : ce terrain est déjà sous contrat avec un autre acheteur.")
            return redirect('web_property_detail', pk=property_id)

    # Création du folio
    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=request.user,
        seller=prop.owner_wallet,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )

    # Simulation de la mise en séquestre des fonds (Processus fiduciaire sécurisé)
    from marketplace.models import Listing
    active_listing = Listing.objects.filter(property=prop, status=Listing.Status.ACTIVE).first()

    messages.success(request, f"Dossier ouvert chez Me {notary.name}. Votre achat est maintenant sécurisé par notre plateforme.")
    return redirect('web_transaction_status', folio_id=folio.id)

@login_required
def web_transaction_status(request, folio_id):
    """Suivi en temps réel de la transaction (Les 6 étapes)."""
    folio = get_object_or_404(TransactionFolio, id=folio_id)
    
    # Sécurité : Seules les parties ou le notaire rattaché peuvent voir
    is_partie = request.user == folio.buyer or request.user == folio.seller
    is_notaire_folio = hasattr(request.user, 'notary_profile') and request.user.notary_profile == folio.notary
    
    if not (is_partie or is_notaire_folio):
        messages.error(request, "Accès non autorisé à ce dossier.")
        return redirect('web_marketplace')

    from marketplace.models import Listing, Notification
    listing = Listing.objects.filter(property=folio.property, status__in=[Listing.Status.ACTIVE, Listing.Status.SOLD]).first()

    # Marquer les notifications de type TRANSACTION_UPDATE pour ce folio comme lues
    from django.utils import timezone
    Notification.objects.filter(
        user=request.user,
        type='TRANSACTION_UPDATE',
        payload__folio_id=str(folio.id),
        read_at__isnull=True
    ).update(read_at=timezone.now())

    return render(request, 'notaries/transaction_status.html', {
        'folio': folio,
        'steps': TransactionFolio.Step.choices,
        'current_step': folio.status,
        'listing': listing
    })

@login_required
def user_transactions(request):
    """Liste de toutes les transactions de l'utilisateur (achats et ventes)."""
    purchases = TransactionFolio.objects.filter(buyer=request.user).order_by('-created_at')
    sales = TransactionFolio.objects.filter(seller=request.user).order_by('-created_at')
    
    return render(request, 'notaries/my_transactions.html', {
        'purchases': purchases,
        'sales': sales
    })

@login_required
@notary_required
def notary_dashboard(request):
    """Tableau de bord pour le notaire : liste des dossiers à traiter."""
    notary = request.user.notary_profile
    transactions = TransactionFolio.objects.filter(notary=notary).order_by('-updated_at')
    
    return render(request, 'notaries/notary_dashboard.html', {
        'notary': notary,
        'transactions': transactions
    })

@login_required
@notary_required
def update_transaction_step(request, folio_id):
    """Permet au notaire de valider une étape de la chaîne de valeur."""
    notary = request.user.notary_profile
    folio = get_object_or_404(TransactionFolio, id=folio_id, notary=notary)
    
    if request.method == 'POST':
        next_step = request.POST.get('next_step')
        andf_number = request.POST.get('andf_number')
        
        if next_step in dict(TransactionFolio.Step.choices):
            try:
                folio.status = next_step
                
                # Mise à jour des timestamps spécifiques
                now = timezone.now()
                if next_step == TransactionFolio.Step.STEP2_ID_VERIFIED:
                    folio.step2_verified_at = now
                elif next_step == TransactionFolio.Step.STEP3_DEED_SIGNED:
                    folio.step3_signed_at = now
                elif next_step == TransactionFolio.Step.STEP4_ANDF_DEPOSITED:
                    folio.step4_deposited_at = now
                    if andf_number:
                        folio.andf_dossier_number = andf_number
                elif next_step == TransactionFolio.Step.STEP5_TITLE_MODIFIED:
                    folio.step5_modified_at = now
                elif next_step == TransactionFolio.Step.STEP6_COMPLETED:
                    folio.step6_completed_at = now
                    
                    # Mise à jour finale de la propriété physique (Simulation Mutation Cadastre)
                    prop = folio.property
                    prop.owner_wallet = folio.buyer
                    prop.save()
                    
                    # Clôture de l'annonce sur la marketplace
                    from marketplace.models import Listing
                    Listing.objects.filter(property=prop, status=Listing.Status.ACTIVE).update(status=Listing.Status.SOLD)
                    
                folio.save()
                
                # Déclencher les notifications (Email/SMS simulation)
                notify_transaction_update(folio)
                
                messages.success(request, f"Dossier mis à jour avec succès : {folio.get_status_display()}")
            except Exception as e:
                messages.error(request, f"❌ Erreur lors de la mise à jour : {str(e)}")
            
    return redirect('notary_dashboard')
