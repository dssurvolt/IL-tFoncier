import os
import django
import uuid

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from notaries.models import Notary, TransactionFolio
from marketplace.models import Listing

def setup_rakib_test():
    print("🚀 Reconstruction du scénario propre : Rakib, Ousmane et Me AKOFFODJI...")
    
    # 1. ACHETEUR : Rakib
    # Note: On garde le full_name comme pivot car son mail a pu changer
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if not rakib:
        rakib = User.objects.create_user(
            email="rakib.sobabe@ilot.bj",
            password="Rakib2026Password",
            full_name="Rakib SOBABE",
            role=User.Role.USER,
            wallet_address=f"0x{uuid.uuid4().hex[:40]}"
        )
        print(f"✅ Rakib créé.")
    else:
        rakib.set_password("Rakib2026Password")
        if not rakib.wallet_address:
            rakib.wallet_address = f"0x{uuid.uuid4().hex[:40]}"
        rakib.save()
        print(f"ℹ️ Rakib réinitialisé.")

    # 2. VENDEUR : Ousmane
    ousmane, created = User.objects.get_or_create(
        email="ousmane.alfa@exemple.com",
        defaults={
            'full_name': "Ousmane ALFA",
            'role': User.Role.USER,
            'wallet_address': f"0x{uuid.uuid4().hex[:40]}"
        }
    )
    ousmane.set_password("Ousmane2026Password")
    ousmane.save()
    if created: print("✅ Ousmane créé.")
    else: print("ℹ️ Ousmane réinitialisé.")

    # 3. NOTAIRE : Me Akoffodji
    ak_user = User.objects.filter(email="jp.akoffodji@notariat.bj").first()
    if not ak_user:
        # Normalement créé par create_akoffodji.py
        print("❌ Erreur: Me Akoffodji n'existe pas. Lancez create_akoffodji.py d'abord.")
        return
        
    ak_notary = Notary.objects.get(user=ak_user)

    # 4. PROPRIÉTÉ : Lot 405
    prop, created = Property.objects.get_or_create(
        village="Lot 405 - Cadjèhoun",
        defaults={
            'owner_wallet': ousmane,
            'district': "Cotonou 12e",
            'status': Property.Status.ON_CHAIN,
            'gps_centroid': {"lat": 6.353, "lng": 2.392},
            'gps_boundaries': [{"lat": 6.353, "lng": 2.392}, {"lat": 6.354, "lng": 2.392}]
        }
    )
    if not created:
        prop.owner_wallet = ousmane
        prop.save()

    # S'assurer qu'il y a un témoin (Filtre Marketplace iLôt)
    from land_registry.models import PropertyWitness
    PropertyWitness.objects.get_or_create(
        property=prop,
        first_name="Témoin",
        last_name="Certifié",
        defaults={
            'phone': "+229 01 00 00 00",
            'birth_date': "1985-05-15",
            'gender': 'M'
        }
    )

    # 5. ANNONCE
    listing, created = Listing.objects.get_or_create(
        property=prop,
        defaults={
            'price_fiat': 15000000,
            'price_crypto': 1.2,
            'status': Listing.Status.ACTIVE
        }
    )
    if not created:
        listing.status = Listing.Status.ACTIVE
        listing.price_fiat = 15000000
        listing.save()

    # 6. FOLIO UNIQUE
    TransactionFolio.objects.filter(property=prop).delete()
    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=rakib,
        seller=ousmane,
        notary=ak_notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )
    
    print(f"\n✨ SCÉNARIO PRÊT ! ✨")
    print(f"📦 Folio ID : {folio.id}")
    print(f"👤 Acheteur (Rakib) : {rakib.email} / Rakib2026Password")
    print(f"👤 Vendeur (Ousmane) : {ousmane.email} / Ousmane2026Password")
    print(f"⚖️ Notaire (Akoffodji) : {ak_user.email} / Notaire2026Password")

if __name__ == "__main__":
    setup_rakib_test()
