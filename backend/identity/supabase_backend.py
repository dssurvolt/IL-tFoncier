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
            # 2. Valider le JWT (Support de ES256 / ECC P-256)
            import jwt
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.backends import default_backend
            import base64
            
            try:
                # Reconstruction de la Clé Publique depuis le JWK (x, y)
                jwk = settings.SUPABASE_JWK
                
                def b64_decode(data):
                    missing_padding = len(data) % 4
                    if missing_padding:
                        data += '=' * (4 - missing_padding)
                    return base64.urlsafe_b64decode(data)

                x_bytes = b64_decode(jwk["x"])
                y_bytes = b64_decode(jwk["y"])
                
                x = int.from_bytes(x_bytes, "big")
                y = int.from_bytes(y_bytes, "big")
                
                public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1())
                public_key = public_numbers.public_key(default_backend())

                # Décodage avec l'algorithme ES256 de Supabase
                payload = jwt.decode(
                    token, 
                    public_key, 
                    algorithms=["ES256"], 
                    options={"verify_aud": False}
                )
            except Exception as ecc_err:
                # Fallback sur HS256 au cas où
                print(f"⚠️ ECC failed ({ecc_err}), attempting HS256 fallback...")
                try:
                    payload = jwt.decode(
                        token, 
                        settings.SUPABASE_JWT_SECRET, 
                        algorithms=["HS256"], 
                        options={"verify_aud": False}
                    )
                except Exception as hs_err:
                    print(f"❌ Tous les décodages ont échoué. ECC: {ecc_err} | HS256: {hs_err}")
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
