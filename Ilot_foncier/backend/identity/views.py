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
    
    def post(self, request, action=None):
        if action == 'register':
            return self.register(request)
        elif action == 'login':
            return self.login(request)
        elif action == 'logout':
            return self.logout(request)
            return self.login(request)
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
            
            # Créer l'utilisateur
            import secrets
            wallet_address = f'0x{secrets.token_hex(20)}'
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                country=country,
                district=district,
                role=User.Role.USER,
                wallet_address=wallet_address
            )
            
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
                # Create Django Session
                login(request, user)
                # Auto-fix wallet address for Legacy Users
                if not user.wallet_address:
                    import secrets
                    user.wallet_address = f'0x{secrets.token_hex(20)}'
                    user.save()
                # Auto-login
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
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
