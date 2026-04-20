import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from marketplace.models import Notification

def transfer_admin_data():
    OLD_EMAIL = "admin@ilotfoncier.com"
    NEW_EMAIL = "rakib.sobabe@epitech.eu"
    
    try:
        old_user = User.objects.get(email=OLD_EMAIL)
        new_user = User.objects.get(email=NEW_EMAIL)
        
        print(f"🔄 Début du transfert : {OLD_EMAIL} -> {NEW_EMAIL}")
        
        # 1. Transférer les propriétés
        props_count = Property.objects.filter(owner_wallet=old_user).update(owner_wallet=new_user)
        print(f"✅ {props_count} propriétés transférées.")
        
        # 2. Transférer les notifications
        notif_count = Notification.objects.filter(user=old_user).update(user=new_user)
        print(f"✅ {notif_count} notifications transférées.")
        
        # 3. Donner les droits Admin au nouveau compte
        new_user.is_staff = True
        new_user.is_superuser = True
        new_user.role = old_user.role # NOTARY ou ADMIN selon le cas
        new_user.save()
        print(f"👑 Droits d'administrateur accordés à {NEW_EMAIL}.")
        
        # 4. Supprimer l'ancien compte pour éviter les confusions (optionnel mais recommandé)
        # old_user.delete()
        # print(f"🗑️ Ancien compte {OLD_EMAIL} archivé.")
        
        print("✨ OPÉRATION RÉUSSIE !")
        
    except User.DoesNotExist:
        print("❌ Erreur : L'un des deux comptes n'existe pas en base de données.")
    except Exception as e:
        print(f"❌ Erreur lors du transfert : {e}")

if __name__ == "__main__":
    transfer_admin_data()
