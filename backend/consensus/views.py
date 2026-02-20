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

def web_validation(request):
    """Vue HTML pour le simulateur de consensus."""
    return render(request, 'validation.html')

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

            return JsonResponse({'id': str(val_req.id), 'status': 'OPEN'}, status=201)
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
