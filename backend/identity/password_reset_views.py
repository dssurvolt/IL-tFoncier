import json
import secrets
from datetime import timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from identity.models import User, PasswordResetToken

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetAPI(View):
    """API pour la réinitialisation de mot de passe"""
    
    def post(self, request, action=None):
        if action == 'request':
            return self.request_reset(request)
        elif action == 'confirm':
            return self.confirm_reset(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
    
    def request_reset(self, request):
        """Demande de réinitialisation - Envoie un email avec le token"""
        try:
            body = json.loads(request.body)
            email = body.get('email', '').strip().lower()
            
            if not email:
                return JsonResponse({
                    'error': 'Email requis'
                }, status=400)
            
            # Chercher l'utilisateur
            try:
                user = User.objects.get(email=email)
                
                # Générer un token sécurisé
                token = secrets.token_urlsafe(32)
                
                # Créer le token de réinitialisation (valide 1 heure)
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=timezone.now() + timedelta(hours=1)
                )
                
                # Construire le lien de réinitialisation
                reset_link = f"{request.scheme}://{request.get_host()}/password-reset/confirm/?token={token}"
                
                # Envoyer l'email
                try:
                    send_mail(
                        subject='iLôt Foncier - Réinitialisation de votre mot de passe',
                        message=f"""
Bonjour {user.full_name or 'Utilisateur'},

Vous avez demandé la réinitialisation de votre mot de passe sur iLôt Foncier.

Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :
{reset_link}

Ce lien est valide pendant 1 heure.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe iLôt Foncier
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    print(f"✉️  Email envoyé à {user.email}")
                    print(f"🔗 Lien de réinitialisation : {reset_link}")
                except Exception as e:
                    # En développement, afficher le lien dans la console
                    print(f"⚠️  Erreur d'envoi d'email (mode dev) : {e}")
                    print(f"🔗 Lien de réinitialisation : {reset_link}")
                
            except User.DoesNotExist:
                # Ne pas révéler si l'email existe ou non (sécurité)
                pass
            
            # Toujours retourner succès (même si l'email n'existe pas)
            return JsonResponse({
                'success': True,
                'message': 'Si cet email est enregistré, vous recevrez un lien de réinitialisation'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def confirm_reset(self, request):
        """Confirme la réinitialisation avec le token et le nouveau mot de passe"""
        try:
            body = json.loads(request.body)
            token = body.get('token', '')
            new_password = body.get('new_password', '')
            
            if not token or not new_password:
                return JsonResponse({
                    'error': 'Token et nouveau mot de passe requis'
                }, status=400)
            
            # Valider le nouveau mot de passe
            import re
            
            if len(new_password) < 8:
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins 8 caractères'
                }, status=400)
            
            if not re.search(r'[A-Z]', new_password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins une lettre majuscule'
                }, status=400)
            
            if not re.search(r'[a-z]', new_password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins une lettre minuscule'
                }, status=400)
            
            if not re.search(r'[0-9]', new_password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins un chiffre'
                }, status=400)
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*)'
                }, status=400)
            
            # Chercher le token
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid():
                    return JsonResponse({
                        'error': 'Ce lien de réinitialisation a expiré ou a déjà été utilisé'
                    }, status=400)
                
                # Réinitialiser le mot de passe
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Marquer le token comme utilisé
                reset_token.mark_as_used()
                
                # Invalider tous les autres tokens de cet utilisateur
                PasswordResetToken.objects.filter(
                    user=user,
                    used=False
                ).exclude(id=reset_token.id).update(used=True)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Mot de passe réinitialisé avec succès',
                    'user_id': str(user.id),
                    'email': user.email
                })
                
            except PasswordResetToken.DoesNotExist:
                return JsonResponse({
                    'error': 'Token invalide'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
