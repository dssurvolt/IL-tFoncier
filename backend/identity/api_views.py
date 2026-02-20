from django.http import JsonResponse
from django.views import View
from identity.models import User

class UserProfileAPI(View):
    """API pour récupérer le profil utilisateur"""
    
    def get(self, request, wallet=None):
        try:
            if wallet:
                user = User.objects.get(wallet_address=wallet.lower())
            else:
                return JsonResponse({'error': 'Wallet address required'}, status=400)
            
            return JsonResponse({
                'id': str(user.id),
                'email': user.email,
                'wallet_address': user.wallet_address,
                'full_name': user.full_name,
                'role': user.role,
                'country': user.country,
                'district': user.district,
                'village': user.village,
                'reputation_score': user.reputation_score,
                'created_at': user.created_at.isoformat()
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
