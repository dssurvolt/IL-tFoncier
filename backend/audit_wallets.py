import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import TransactionFolio
from land_registry.models import Property

def audit_wallets():
    print("--- Audit Wallets ---")
    users_no_wallet = User.objects.filter(wallet_address__in=[None, ''])
    print(f"Users without wallet: {users_no_wallet.count()}")
    for u in users_no_wallet:
        print(f"  - {u.email} ({u.full_name})")

    folios = TransactionFolio.objects.all()
    for f in folios:
        problems = []
        if not f.buyer.wallet_address:
            problems.append(f"Buyer ({f.buyer.email}) has no wallet")
        if not f.seller.wallet_address:
            problems.append(f"Seller ({f.seller.email}) has no wallet")
        
        if problems:
            print(f"Folio {f.id} (Property: {f.property.village})")
            for p in problems:
                print(f"  - {p}")

    props = Property.objects.all()
    for p in props:
        if not p.owner_wallet.wallet_address:
            print(f"Property {p.id} ({p.village}) owner {p.owner_wallet.email} has no wallet!")

if __name__ == "__main__":
    audit_wallets()
