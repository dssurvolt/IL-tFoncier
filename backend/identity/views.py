import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from identity.models import User

@method_decorator(csrf_exempt, name='dispatch')
class AuthAPI(View):
    """API pour l'authentification (Login/Register)"""
    
    def get(self, request, action=None):
        if action == 'temp-unlock-admin':
            return self.temp_unlock_admin(request)
        return JsonResponse({'error': 'GET not supported for this action'}, status=405)

    def post(self, request, action=None):
        if action == 'register':
            return self.register(request)
        elif action == 'login':
            return self.login(request)
        elif action == 'supabase-login':
            return self.supabase_login(request)
        elif action == 'logout':
            return self.logout(request)
        elif action == 'temp-unlock-admin':
            return self.temp_unlock_admin(request)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
    
    def register(self, request):
        """Inscription d'un nouvel utilisateur"""
        try:
            body = json.loads(request.body)
            email = body.get('email', '').strip().lower()
            password = body.get('password', '')
            full_name = body.get('full_name', '').strip()
            country = body.get('country', 'Benin')
            district = body.get('district')
            village = body.get('village')
            birth_date = body.get('birth_date')
            
            # Validation
            if not email or not password or not full_name:
                return JsonResponse({
                    'error': 'Email, mot de passe et nom complet sont requis'
                }, status=400)
            
            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'error': 'Un compte existe déjà avec cet email'
                }, status=400)
            
            # Validation robuste du mot de passe
            import re
            
            if len(password) < 8:
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins 8 caractères'
                }, status=400)
            
            if not re.search(r'[A-Z]', password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins une lettre majuscule'
                }, status=400)
            
            if not re.search(r'[a-z]', password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins une lettre minuscule'
                }, status=400)
            
            if not re.search(r'[0-9]', password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins un chiffre'
                }, status=400)
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return JsonResponse({
                    'error': 'Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*)'
                }, status=400)
            
            user_data = {
                'email': email,
                'password': password,
                'full_name': full_name,
                'country': country,
                'district': district,
                'role': User.Role.USER
            }
            if village: user_data['village'] = village
            if birth_date: user_data['birth_date'] = birth_date
            
            user = User.objects.create_user(**user_data)
            
            # Envoi de l'email de bienvenue (Tentative)
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = "Bienvenue sur iLôt Foncier ! 🌍"
                message = f"Bonjour {user.full_name},\n\nVotre compte a été créé avec succès sur iLôt Foncier. Vous pouvez désormais sécuriser vos terres et participer à la marketplace foncière.\n\nIdentifiant : {user.email}\n\nÉquipe iLôt Foncier."
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=True, # On ne bloque pas l'inscription si le mail échoue
                )
            except Exception as e:
                print(f"Erreur d'envoi d'email : {e}")
            
            # Auto-login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return JsonResponse({
                'success': True,
                'user_id': str(user.id),
                'email': user.email,
                'full_name': user.full_name
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    
    def logout(self, request):
        """Déconnexion de l'utilisateur"""
        from django.contrib.auth import logout
        logout(request)
        return JsonResponse({'success': True, 'message': 'Déconnecté avec succès'})

    def login(self, request):
        """Connexion d'un utilisateur"""
        try:
            body = json.loads(request.body)
            email = body.get('email', '').strip().lower()
            password = body.get('password', '')
            
            if not email or not password:
                return JsonResponse({
                    'error': 'Email et mot de passe requis'
                }, status=400)
            
            # Authentifier l'utilisateur
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                
                # Create Django Session and Login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse({
                    'success': True,
                    'user_id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                })
            else:
                return JsonResponse({
                    'error': 'Email ou mot de passe incorrect'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    def temp_unlock_admin(self, request):
        """
        Route temporaire de secours pour activer l'accès /admin/.
        À SUPPRIMER APRÈS USAGE.
        """
        try:
            from identity.models import User
            user = User.objects.get(email='rakib.sobabe@epitech.eu')
            user.set_password('AdminSelection2026!')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return JsonResponse({'success': 'Compte Admin déverrouillé !'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def supabase_login(self, request):
        """
        Méthode pour échanger un jeton Supabase contre une session Django.
        """
        try:
            body = json.loads(request.body)
            access_token = body.get('access_token')
            
            if not access_token:
                return JsonResponse({'error': 'Token manquant'}, status=400)
            
            # Authentifier via notre nouveau backend
            from django.contrib.auth import authenticate, login
            user = authenticate(request, token=access_token)
            
            if user is not None:
                login(request, user, backend='identity.supabase_backend.SupabaseAuthBackend')
                return JsonResponse({
                    'success': True,
                    'user_id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                })
            else:
                return JsonResponse({'error': 'Token invalide ou utilisateur non trouvé'}, status=401)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
