import json
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from .models import ValidationRequest, WitnessVote
from land_registry.models import Property
from identity.models import User
from utils.chasquid_api import EmailNotifier
from django.conf import settings

from django.shortcuts import render, get_object_or_404
from django.db import transaction
from land_registry.models import Property, PropertyWitness

from identity.decorators import admin_required

@admin_required
def web_validation(request):
    """Vue HTML pour le simulateur de consensus."""
    return render(request, 'validation.html')

def web_witness_confirmation(request):
    """Vue pour qu'un témoin confirme son témoignage via le lien reçu par email."""
    req_id = request.GET.get('req')
    witness_id = request.GET.get('witness')

    if not req_id or not witness_id:
        return render(request, 'witness_confirmation.html', {'error': 'Lien invalide (IDs manquants).'})

    val_req = get_object_or_404(ValidationRequest, id=req_id)
    witness = get_object_or_404(PropertyWitness, id=witness_id, property=val_req.property)

    # Vérifier si ce témoin a déjà voté pour cette demande
    already_voted = WitnessVote.objects.filter(request=val_req, witness_phone=witness.phone).exists()

    if request.method == 'POST':
        if already_voted:
            return render(request, 'witness_confirmation.html', {
                'val_req': val_req,
                'witness': witness,
                'error': 'Vous avez déjà validé ce témoignage.'
            })

        vote_result = request.POST.get('vote') == 'yes'
        # On pourrait demander le numéro de pièce d'identité ici
        id_number = request.POST.get('id_number', 'N/A') 

        try:
            with transaction.atomic():
                # 1. Enregistrer le vote
                WitnessVote.objects.create(
                    request=val_req,
                    witness_full_name=f"{witness.first_name} {witness.last_name}",
                    witness_phone=witness.phone,
                    witness_id_number=id_number,
                    witness_birth_date=witness.birth_date,
                    witness_gps={'lat': 6.36, 'lng': 2.42}, # Simulation GPS
                    vote_result=vote_result,
                    signature='EMAIL_LINK_CONFIRMATION'
                )

                # 2. Marquer le témoin comme confirmé dans le dossier de parcelle
                witness.is_confirmed = True
                witness.save()

                # 3. Vérifier si le consensus est atteint
                positive_votes = val_req.votes.filter(vote_result=True).count()
                total_witnesses = val_req.property.witnesses.count()
                
                # On considère le consensus atteint si tous les témoins ont validé (ou au moins min_witnesses)
                if positive_votes >= val_req.min_witnesses or positive_votes >= total_witnesses:
                    val_req.status = ValidationRequest.Status.COMPLETED
                    val_req.save()
                    
                    prop = val_req.property
                    prop.status = Property.Status.ON_CHAIN
                    prop.save()
                    
                    context = {
                        'success': True,
                        'message': 'Merci ! Votre témoignage a été enregistré. Le consensus est maintenant atteint pour cette parcelle.',
                        'val_req': val_req,
                        'witness': witness
                    }
                else:
                    context = {
                        'success': True,
                        'message': 'Merci ! Votre témoignage a été enregistré. En attente des autres témoins.',
                        'val_req': val_req,
                        'witness': witness
                    }
                return render(request, 'witness_confirmation.html', context)

        except Exception as e:
            return render(request, 'witness_confirmation.html', {
                'val_req': val_req,
                'witness': witness,
                'error': f"Une erreur est survenue lors de l'enregistrement : {str(e)}"
            })

    return render(request, 'witness_confirmation.html', {
        'val_req': val_req,
        'witness': witness,
        'property': val_req.property,
        'already_voted': already_voted
    })

@method_decorator(csrf_exempt, name='dispatch')
class ValidationRequestAPI(View):
    """
    Gère le cycle de vie d'une validation :
    POST /api/validation/request/ : Initier une demande
    POST /api/validation/vote/    : Voter (Témoin)
    """
    
    def post(self, request, action=None):
        if action == 'initiate':
            return self.initiate_validation(request)
        elif action == 'vote':
            return self.submit_vote(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    def initiate_validation(self, request):
        """UC-01: Le propriétaire demande à ses voisins de valider."""
        try:
            body = json.loads(request.body)
            property_id = body.get('property_id')
            requester_wallet = body.get('requester_wallet')
            gps_at_request = body.get('gps_at_request') # {lat, lng}

            # 1. Vérifier que la propriété existe et est en brouillon
            prop = Property.objects.get(id=property_id)
            if prop.status != Property.Status.DRAFT:
                return JsonResponse({'error': 'Property not in DRAFT state'}, status=400)

            # 2. Créer la demande
            val_req = ValidationRequest.objects.create(
                property=prop,
                requester_wallet=requester_wallet,
                gps_at_request=gps_at_request,
                status=ValidationRequest.Status.OPEN
            )
            
            # 3. Mettre à jour le statut de la propriété
            prop.status = Property.Status.VALIDATING
            prop.save()

            # 4. Envoi des Emails via Chasquid
            witnesses = prop.witnesses.all()
            owner_name = prop.owner_wallet.full_name or "Un citoyen iLôt"
            
            for witness in witnesses:
                if witness.email:
                    # Lien de validation simulé (pourrait pointer vers une page dédiée)
                    validation_link = f"{request.scheme}://{request.get_host()}/validation/witness/?req={val_req.id}&witness={witness.id}"
                    
                    EmailNotifier.send_witness_invitation(
                        witness_name=witness.first_name,
                        witness_email=witness.email,
                        owner_name=owner_name,
                        property_id=str(prop.id),
                        validation_link=validation_link
                    )

            return JsonResponse({
                'id': str(val_req.id), 
                'status': 'OPEN',
                'witness_count': witnesses.count()
            }, status=201)
        except Property.DoesNotExist:
            return JsonResponse({'error': 'Parcelle non trouvée.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def submit_vote(self, request):
        """UC-01 (Suite): Un voisin vote avec son identité légale universelle."""
        try:
            body = json.loads(request.body)
            request_id = body.get('request_id')
            
            # Identité Légale Universelle
            witness_name = body.get('witness_name')
            witness_phone = body.get('witness_phone')
            witness_id_number = body.get('witness_id_number')
            witness_birth_date = body.get('witness_birth_date') # YYYY-MM-DD
            
            vote_result = body.get('vote_result')
            witness_gps = body.get('witness_gps', {})
            witness_wallet_addr = body.get('witness_wallet') # Optionnel
            signature = body.get('signature', 'WEB_SIGNATURE_PENDING')
            
            if not all([witness_name, witness_phone, witness_id_number]):
                return JsonResponse({'error': 'Missing legal identity information (Name, Phone, ID Number)'}, status=400)

            # 1. Gérer l'utilisateur (Optionnel/Lien Wallet)
            witness_user = None
            if witness_wallet_addr:
                witness_user, _ = User.objects.get_or_create(
                    wallet_address=witness_wallet_addr, 
                    defaults={'role': User.Role.WITNESS, 'full_name': witness_name}
                )
            
            # 2. Vérifier si la demande est toujours ouverte
            val_req = ValidationRequest.objects.get(id=request_id)
            if val_req.status != ValidationRequest.Status.OPEN:
                return JsonResponse({'error': 'Validation request is already closed'}, status=400)

            # 3. Enregistrer le vote (ID Number = Clé d'unicité)
            try:
                vote = WitnessVote.objects.create(
                    request_id=request_id,
                    witness_full_name=witness_name,
                    witness_phone=witness_phone,
                    witness_id_number=witness_id_number,
                    witness_birth_date=witness_birth_date,
                    witness_wallet=witness_user,
                    witness_gps=witness_gps,
                    vote_result=vote_result,
                    signature=signature
                )
            except Exception as e:
                return JsonResponse({'error': f'Witness (ID {witness_id_number}) has already voted for this request'}, status=400)
            
            # 4. LOGIQUE MÉTIER : Vérifier si le consensus est atteint
            positive_votes = val_req.votes.filter(vote_result=True).count()
            
            if positive_votes >= val_req.min_witnesses:
                val_req.status = ValidationRequest.Status.COMPLETED
                val_req.save()
                
                # Mettre à jour la propriété -> Prêt pour Blockchain
                prop = val_req.property
                prop.status = Property.Status.ON_CHAIN
                prop.save()
                
                return JsonResponse({'status': 'VOTE_RECORDED', 'consensus': 'REACHED'}, status=200)

            return JsonResponse({'status': 'VOTE_RECORDED', 'consensus': 'PENDING'}, status=200)
            
        except ValidationRequest.DoesNotExist:
            return JsonResponse({'error': 'Validation request not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
