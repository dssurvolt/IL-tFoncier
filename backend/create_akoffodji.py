import os
import django
import uuid

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import Notary
from land_registry.models import Property, PropertyWitness

def fix_missing_wallets():
    print("🛠️ Vérification des adresses de portefeuille (wallets)...")
    users_no_wallet = User.objects.filter(wallet_address__in=['', None])
    for u in users_no_wallet:
        u.wallet_address = f"0x{uuid.uuid4().hex[:40]}"
        u.save()
        print(f"✅ Wallet généré pour {u.email} : {u.wallet_address}")

def heal_notaries():
    print("\n⚖️ Réparation des profils Notaires...")
    notaries = Notary.objects.all()
    for n in notaries:
        if not n.user:
            # Essayer de trouver un utilisateur par email
            user = User.objects.filter(email=n.email).first()
            if user:
                n.user = user
                n.save()
                print(f"🔗 Notaire {n.name} lié à l'utilisateur {user.email}")
            else:
                # Créer un utilisateur si manquant
                user_email = n.email or f"notaire_{uuid.uuid4().hex[:8]}@ilot.bj"
                user = User.objects.create_user(
                    email=user_email,
                    password="NotairePassword2026",
                    role=User.Role.NOTARY,
                    full_name=f"Me {n.name}",
                    wallet_address=f"0x{uuid.uuid4().hex[:40]}"
                )
                n.user = user
                n.email = user_email
                n.save()
                print(f"✨ Nouvel utilisateur créé pour Notaire {n.name} : {user_email}")

def create_notary_akoffodji():
    print("\n🚀 Configuration Me Jean-Pierre AKOFFODJI...")
    email = "jp.akoffodji@notariat.bj"
    password = "Notaire2026Password"
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'full_name': "Me Jean-Pierre AKOFFODJI",
            'role': User.Role.NOTARY,
            'wallet_address': f"0x{uuid.uuid4().hex[:40]}"
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Utilisateur créé : {email}")
    else:
        # S'assurer qu'il a un wallet
        if not user.wallet_address:
            user.wallet_address = f"0x{uuid.uuid4().hex[:40]}"
            user.save()
        print(f"ℹ️ Utilisateur existe déjà.")

    notary, created = Notary.objects.get_or_create(
        email=email,
        defaults={
            'user': user,
            'name': "Jean-Pierre AKOFFODJI",
            'office_name': "Étude de Maître AKOFFODJI",
            'license_number': "NOT-BEN-229-0042",
            'phone': "+229 01 95 95 95",
            'address': "Immeuble Le Grand Large, Boulevard Marina, Cotonou",
            'city': "Cotonou",
            'avg_processing_time_days': 25,
            'is_verified': True
        }
    )
    if created:
        print(f"✅ Profil Notaire créé.")
    else:
        if not notary.user:
            notary.user = user
            notary.save()
        print(f"ℹ️ Profil Notaire existe déjà.")
    
    return email, password

def check_and_fix_orphans():
    print("\n🔍 Nettoyage des données incomplètes...")
    
    # Check Users without full_name
    orphans_users = User.objects.filter(full_name__in=['', None])
    for u in orphans_users:
        u.full_name = f"Citoyen {u.email.split('@')[0]}"
        u.save()
        print(f"🛠️ Nom manquant pour {u.email} -> '{u.full_name}'")

    # Check Properties without labels
    orphans_props = Property.objects.filter(village__in=['', None])
    for p in orphans_props:
        p.village = "Parcelle iLôt Sécurisée"
        p.district = p.district or "Zone Résidentielle"
        p.save()
        print(f"🛠️ Village manquant pour Propriété {p.id} -> Fixé")

if __name__ == "__main__":
    fix_missing_wallets()
    heal_notaries()
    create_notary_akoffodji()
    check_and_fix_orphans()
    print("\n🏁 Base de données assainie.")
