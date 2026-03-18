import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property

def run_cleanup():
    print("🚀 Démarrage du nettoyage préventif d'iLôt Foncier...")
    
    users = User.objects.all()
    deleted_users = 0
    
    for user in users:
        is_incomplete = False
        reasons = []
        
        # 1. Vérification de l'utilisateur
        if not user.full_name or user.full_name == "None":
            is_incomplete = True
            reasons.append("Nom complet manquant/invalide")
            
        if not user.wallet_address:
            is_incomplete = True
            reasons.append("Wallet manquant")

        # 2. Vérification des propriétés
        user_properties = Property.objects.filter(owner_wallet=user.wallet_address)
        
        for prop in user_properties:
            prop_incomplete = False
            if not prop.gps_centroid or 'lat' not in prop.gps_centroid:
                prop_incomplete = True
                reasons.append(f"Prop {prop.id}: GPS invalide")
            
            if not prop.gps_boundaries or len(prop.gps_boundaries) < 3:
                prop_incomplete = True
                reasons.append(f"Prop {prop.id}: Limites GPS invalides")
                
            if not prop.village:
                prop_incomplete = True
                reasons.append(f"Prop {prop.id}: Village manquant")

            if prop.media.count() == 0:
                prop_incomplete = True
                reasons.append(f"Prop {prop.id}: Pas de médias")
                
            if prop.witnesses.count() == 0:
                prop_incomplete = True
                reasons.append(f"Prop {prop.id}: Pas de témoins")
            
            if prop_incomplete:
                is_incomplete = True

        if is_incomplete:
            print(f"⚠️ Suppression du compte {user.email}")
            print(f"   Raisons: {', '.join(reasons)}")
            
            # Pour contourner le PROTECT, on supprime manuellement les propriétés rattachées
            user_properties.delete()
            # Puis l'utilisateur
            user.delete()
            deleted_users += 1

    print(f"✅ Nettoyage terminé. Comptes supprimés: {deleted_users}")

if __name__ == '__main__':
    run_cleanup()
