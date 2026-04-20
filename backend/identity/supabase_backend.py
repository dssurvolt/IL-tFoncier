import jwt
from django.conf import settings
from .models import User
from django.contrib.auth.backends import BaseBackend
import uuid

class SupabaseAuthBackend(BaseBackend):
    """
    Backend d'authentification personnalisé pour valider les JWT Supabase.
    """
    
    def authenticate(self, request, token=None):
        if not token:
            return None
        
        try:
            # 1. Décoder le JWT Supabase
            # Note: Supabase utilise la JWT_SECRET pour signer ses tokens (HS256 par défaut)
            payload = jwt.decode(
                token, 
                settings.SUPABASE_JWT_SECRET, 
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # 2. Récupérer les infos de l'utilisateur
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id:
                return None
            
            # 3. Récupérer ou créer l'utilisateur dans Django
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # Si l'utilisateur n'existe pas encore dans Django, on le crée
                user = User.objects.create(
                    id=uuid.UUID(user_id),
                    email=email,
                    full_name=payload.get("user_metadata", {}).get("full_name", email),
                    role=User.Role.USER
                )
                user.set_unusable_password() # On délègue le password à Supabase
                user.save()
            
            return user
            
        except Exception as e:
            print(f"❌ Erreur Auth Supabase : {e}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
