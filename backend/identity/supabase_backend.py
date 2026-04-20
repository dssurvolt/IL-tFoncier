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
            # 2. Valider le JWT avec le Secret Supabase
            import jwt
            try:
                payload = jwt.decode(
                    token, 
                    settings.SUPABASE_JWT_SECRET, 
                    algorithms=["HS256"], 
                    options={"verify_aud": False}
                )
            except Exception as jwt_err:
                print(f"❌ Erreur Décodage JWT : {jwt_err}")
                return None

            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                print("❌ JWT incomplet : sub ou email manquant")
                return None
            
            # 3. Récupérer ou créer l'utilisateur dans Django
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # RECHERCHE PAR EMAIL (Migration Intelligente)
                # Si l'utilisateur existe déjà avec cet email, on fusionne !
                user = User.objects.filter(email=email).first()
                if user:
                    print(f"🔄 Migration : Fusion du profil {email} avec Supabase ID {user_id}")
                    # On met à jour l'ID Django pour qu'il soit identique à Supabase (si possible)
                    # Note: En PostgreSQL, changer une PK peut être complexe, 
                    # mais ici on va tenter une mise à jour directe si aucune contrainte ne bloque.
                    try:
                        User.objects.filter(pk=user.pk).update(id=user_id)
                        user = User.objects.get(id=user_id)
                    except Exception as migration_error:
                        print(f"⚠️ Alerte : Impossible de changer l'ID, on garde l'ID actuel. {migration_error}")
                else:
                    # Création d'un tout nouveau profil
                    user = User.objects.create(
                        id=uuid.UUID(user_id),
                        email=email,
                        full_name=payload.get("user_metadata", {}).get("full_name", email),
                        role=User.Role.USER
                    )
                
                user.set_unusable_password() 
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
