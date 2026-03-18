import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from identity.decorators import admin_required
from .models import Listing, MarketplaceInquiry, MarketplaceView, ChatRoom, ChatMessage, Notification
from land_registry.models import Property
from identity.models import User
from django.utils import timezone
from datetime import timedelta
from notaries.models import Notary

def web_marketplace(request):
    """Vue HTML pour la Marketplace citoyenne."""
    # Filtre de Qualité iLôt : Seules les annonces avec au moins un témoin sont affichées
    listings = Listing.objects.filter(
        status=Listing.Status.ACTIVE
    ).annotate(
        witness_count=Count('property__witnesses')
    ).filter(
        witness_count__gt=0
    ).select_related('property', 'property__owner_wallet').prefetch_related('property__media')
    
    # Traçabilité accrue : Enregistrement de la consultation de la page d'accueil
    try:
        user = request.user if request.user.is_authenticated else None
        MarketplaceView.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            view_type='MARKETPLACE_HOME'
        )
    except Exception as e:
        print(f"Erreur tracking MarketplaceView: {e}")

    # Préparation des données pour la carte JS (Sécurisée via json_script)
    listings_data = []
    for l in listings:
        listings_data.append({
            'id': str(l.property.id), # On utilise l'ID de la propriété pour le lien technique
            'lat': float(l.property.gps_centroid.get('lat', 0)),
            'lng': float(l.property.gps_centroid.get('lng', 0)),
            'price_fiat': f"{l.price_fiat:,}",
            'village': l.property.village or "Parcelle iLôt",
            'is_certified': l.property.is_certified,
            'is_under_contract': l.is_under_contract
        })
        
    # Récupération de quelques notaires certifiés pour rassurer l'acheteur
    featured_notaries = Notary.objects.filter(is_verified=True)[:3]
        
    return render(request, 'marketplace.html', {
        'listings': listings,
        'listings_json': listings_data,
        'featured_notaries': featured_notaries
    })

@login_required
def web_create_listing(request, property_id):
    """Vue HTML pour mettre un terrain en vente."""
    try:
        prop = Property.objects.get(id=property_id)
        
        # Sécurité : Seul le propriétaire peut voir ce formulaire
        if request.user.is_authenticated and prop.owner_wallet != request.user:
            return redirect('login_home')
            
        return render(request, 'create_listing.html', {
            'property': prop,
            'user': request.user if request.user.is_authenticated else prop.owner_wallet
        })
    except Property.DoesNotExist:
        return redirect('web_marketplace')

@method_decorator(csrf_exempt, name='dispatch')
class ListingListAPI(View):
    """
    API Endpoint: /api/marketplace/listings/
    GET: Liste les terrains à vendre
    POST: Mettre un terrain en vente
    """
    def get(self, request):
        listings = Listing.objects.filter(status=Listing.Status.ACTIVE)
        data = []
        for l in listings:
            data.append({
                'id': str(l.id),
                'property_id': str(l.property.id),
                'price_fiat': str(l.price_fiat),
                'price_crypto': str(l.price_crypto),
                'seller': l.property.owner_wallet.wallet_address
            })
        return JsonResponse({'count': len(data), 'results': data})

    def post(self, request):
        try:
            body = json.loads(request.body)
            property_id = body.get('property_id')
            seller_wallet = body.get('seller_wallet')
            price_fiat = body.get('price_fiat')
            price_crypto = body.get('price_crypto')

            # 1. Vérifier l'existence de la propriété
            try:
                prop = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'error': 'Property not found'}, status=404)

            # 2. RÈGLE MÉTIER : Seules les propriétés validées ou en attestation peuvent être listées
            if prop.status not in [Property.Status.ON_CHAIN, Property.Status.PENDING_SURVEYOR]:
                return JsonResponse({'error': 'Only validated or pending surveyor properties can be listed for sale'}, status=400)

            # 3. RÈGLE MÉTIER : Le vendeur doit être le propriétaire
            if prop.owner_wallet.wallet_address != seller_wallet:
                return JsonResponse({'error': 'Only the owner can list this property'}, status=403)
            
            # 4. RÈGLE D'INTÉGRITÉ iLÔT : Témoins obligatoires
            if prop.witnesses.count() == 0:
                return JsonResponse({'error': 'La parcelle ne peut pas être mise en vente sans au moins un témoin certifié.'}, status=400)

            # 5. Vérifier si une offre active existe déjà
            if Listing.objects.filter(property=prop, status=Listing.Status.ACTIVE).exists():
                return JsonResponse({'error': 'Property is already listed for sale'}, status=400)

            # 5. Création de l'offre
            listing = Listing.objects.create(
                property=prop,
                price_fiat=price_fiat,
                price_crypto=price_crypto,
                status=Listing.Status.ACTIVE
            )
            return JsonResponse({'id': str(listing.id), 'status': 'ACTIVE'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MarketplaceInquiryAPI(View):
    """API pour enregistrer une demande d'info (Métrique PMF)."""
    def post(self, request):
        try:
            body = json.loads(request.body)
            listing_id = body.get('listing_id')
            user_id = body.get('user_id')

            listing = Listing.objects.get(id=listing_id)
            user = User.objects.get(id=user_id)

            MarketplaceInquiry.objects.get_or_create(user=user, listing=listing)
            return JsonResponse({'success': True}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@admin_required
def pmf_dashboard(request):
    """Dashboard PMF enrichi : Traçabilité et Cohortes."""
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    
    # 0. Filtrage des Utilisateurs Réels (Exclure tests, staff, example.com)
    real_users = User.objects.exclude(email__icontains='test')\
                             .exclude(email__endswith='@example.com')\
                             .exclude(is_staff=True)\
                             .exclude(is_superuser=True)
    
    # 1. Métriques Globales
    total_users = real_users.count()
    users_with_inquiries = MarketplaceInquiry.objects.filter(
        user__in=real_users,
        created_at__gte=last_7_days
    ).values('user').distinct().count()
    pmf_percentage = (users_with_inquiries / total_users * 100) if total_users > 0 else 0

    # 2. Traçabilité : Dernier journal d'activité (Demandes + Vues)
    recent_inquiries = MarketplaceInquiry.objects.filter(user__in=real_users)\
                                                 .select_related('user', 'listing', 'listing__property')\
                                                 .order_by('-created_at')[:15]
    recent_views = MarketplaceView.objects.select_related('user', 'property').order_by('-created_at')[:15]

    # 3. Analyse par Cohortes Hebdomadaires (12 dernières semaines)
    cohorts_data = []
    for i in range(12, -1, -1):
        # Début de la semaine i (Lundi)
        start_of_this_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        target_week_start = start_of_this_week - timedelta(weeks=i)
        target_week_end = target_week_start + timedelta(weeks=1)
        
        cohort_users = real_users.filter(date_joined__gte=target_week_start, date_joined__lt=target_week_end)
        cohort_count = cohort_users.count()
        
        if cohort_count > 0:
            retention_row = []
            # On suit sur 12 semaines (W0 à W11)
            for w in range(12):
                w_start = target_week_start + timedelta(weeks=w)
                w_end = w_start + timedelta(weeks=1)
                
                if w_start > now:
                    retention_row.append(None) # Futur
                    continue
                
                engaged_in_week = MarketplaceInquiry.objects.filter(
                    user__in=cohort_users,
                    created_at__gte=w_start,
                    created_at__lt=w_end
                ).values('user').distinct().count()
                
                rate = round((engaged_in_week / cohort_count * 100), 1)
                retention_row.append(rate)
            
            cohorts_data.append({
                'label': f"Semaine du {target_week_start.strftime('%d/%m/%Y')}",
                'size': cohort_count,
                'retention': retention_row
            })

    # 4. Indicateur Global [Customer Success Leading Indicator]
    # Seuil : 70% des clients font une demande dans les 2 premiers mois (60 jours)
    # On ne regarde que les utilisateurs inscrits depuis au moins 60 jours
    eligible_users_for_indicator = real_users.filter(date_joined__lte=now - timedelta(days=60))
    total_eligible = eligible_users_for_indicator.count()
    success_count = 0
    if total_eligible > 0:
        for u in eligible_users_for_indicator:
            # A fait une demande dans les 60 jours suivant son inscription ?
            has_inquiry = MarketplaceInquiry.objects.filter(
                user=u,
                created_at__lte=u.date_joined + timedelta(days=60)
            ).exists()
            if has_inquiry:
                success_count += 1
        
        success_rate = (success_count / total_eligible * 100)
    else:
        success_rate = 0
        
    leading_indicator = success_rate >= 70

    return render(request, 'pmf_dashboard.html', {
        'total_users': total_users,
        'users_with_inquiries': users_with_inquiries,
        'pmf_percentage': round(pmf_percentage, 1),
        'goal': 70,
        'recent_inquiries': recent_inquiries,
        'recent_views': recent_views,
        'cohorts': cohorts_data,
        'leading_indicator': leading_indicator,
        'success_rate': round(success_rate, 1)
    })

# --- Système de Chat Privé ---

@login_required
def web_start_chat(request, listing_id):
    """Initialise ou récupère une discussion entre acheteur et vendeur."""
    listing = get_object_or_404(Listing, id=listing_id)
    seller = listing.property.owner_wallet
    buyer = request.user

    if buyer == seller:
        messages.error(request, "Vous ne pouvez pas démarrer une discussion sur votre propre terrain.")
        return redirect('web_marketplace')

    room, created = ChatRoom.objects.get_or_create(
        listing=listing,
        buyer=buyer,
        seller=seller
    )
    return redirect('web_chat_room', room_id=room.id)

@login_required
def web_chat_room(request, room_id):
    """Affiche l'interface de discussion privée."""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Sécurité : Seuls l'acheteur et le vendeur de cette room y ont accès
    if request.user != room.buyer and request.user != room.seller:
        messages.error(request, "Accès non autorisé à cette discussion.")
        return redirect('web_marketplace')

    chat_messages = room.messages.all()
    
    # Marquer les messages entrants comme lus
    room.messages.exclude(sender=request.user).update(is_read=True)
    
    # Marquer les notifications de type NEW_MESSAGE pour cette room comme lues
    from marketplace.models import Notification
    Notification.objects.filter(
        user_wallet=request.user, 
        type='NEW_MESSAGE',
        payload__room_id=str(room.id),
        read_at__isnull=True
    ).update(read_at=timezone.now())

    other_user = room.seller if request.user == room.buyer else room.buyer

    return render(request, 'marketplace/chat_room.html', {
        'room': room,
        'chat_messages': chat_messages,
        'other_user': other_user,
        'user': request.user
    })

import re

def anonymize_content(text):
    """
    Détecte et masque les emails et numéros de téléphone (Format Bénin et International).
    """
    # Masquage Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL MASQUÉ PAR SÉCURITÉ]', text)
    
    # Masquage Téléphones (Détecte les suites de 8 à 15 chiffres avec espaces/points)
    # Pattern spécifique pour éviter de bloquer les prix ou IDs
    phone_pattern = r'(\+?\d[\s\.-]?){8,}'
    
    # On ne masque que si ça ressemble vraiment à un numéro de contact (pas un prix de 1.000.000)
    if not re.search(r'\d{7,}.*FCFA', text, re.IGNORECASE):
        text = re.sub(phone_pattern, '[CONTACT MASQUÉ PAR SÉCURITÉ]', text)
    
    return text

@method_decorator(csrf_exempt, name='dispatch')
class SendMessageAPI(View):
    """API pour l'envoi de messages en temps réel (AJAX)."""
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        try:
            # Support à la fois JSON et Multipart Form Data
            if request.content_type == 'application/json':
                body = json.loads(request.body)
                room_id = body.get('room_id')
                content = body.get('content')
                attachment = None
            else:
                room_id = request.POST.get('room_id')
                content = request.POST.get('content')
                attachment = request.FILES.get('attachment')
            
            if not content and not attachment:
                return JsonResponse({'error': 'Message vide'}, status=400)
            
            # Application du iLôt Shield si contenu texte présent
            clean_content = anonymize_content(content) if content else ""
                
            room = ChatRoom.objects.get(id=room_id)
            if request.user != room.buyer and request.user != room.seller:
                return JsonResponse({'error': 'Interdit'}, status=403)
            
            message = ChatMessage.objects.create(
                room=room,
                sender=request.user,
                content=clean_content,
                attachment=attachment
            )
            
            # Forcer la mise à jour du timestamp de la room
            room.save() 

            # NOTIFICATION : Alerter le destinataire
            receiver = room.seller if request.user == room.buyer else room.buyer
            notif_msg = clean_content if clean_content else "📷 Pièce jointe envoyée"
            Notification.objects.create(
                user_wallet=receiver,
                type='NEW_MESSAGE',
                payload={
                    'title': f"💬 Message de {request.user.full_name}",
                    'message': notif_msg[:60] + "..." if len(notif_msg) > 60 else notif_msg,
                    'room_id': str(room.id)
                }
            )

            return JsonResponse({
                'id': str(message.id),
                'sender': message.sender.full_name,
                'content': message.content,
                'attachment_url': message.attachment.url if message.attachment else None,
                'created_at': message.created_at.strftime("%H:%M")
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_unread_notifications_count(request):
    """API ultra-légère pour le polling des notifications."""
    count = Notification.objects.filter(user_wallet=request.user, read_at__isnull=True).count()
    return JsonResponse({'count': count})

@login_required
def web_my_chats(request):
    """Affiche la liste des discussions actives de l'utilisateur."""
    rooms = ChatRoom.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-updated_at')
    
    return render(request, 'marketplace/my_chats.html', {
        'rooms': rooms
    })
