import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from notaries.models import TransactionFolio, Notary
from marketplace.models import Notification

def check_integrity():
    print("--- Data Integrity Check ---")
    
    # 1. Check Users and Wallets
    users = User.objects.all()
    users_no_wallet = []
    for u in users:
        if not u.wallet_address:
            users_no_wallet.append(u)
    
    print(f"Total Users: {users.count()}")
    print(f"Users without wallet: {len(users_no_wallet)}")
    for u in users_no_wallet:
        print(f"  - {u.email} (Role: {u.role})")

    # 2. Check Property Owners
    props = Property.objects.all()
    broken_props = []
    for p in props:
        # Check if the owner_wallet (which is a FK to User.wallet_address) actually points to something
        try:
            owner = p.owner_wallet
            if not owner.wallet_address:
                 print(f"  [!] Property {p.village} owner {owner.email} HAS NO WALLET but is linked!")
        except User.DoesNotExist:
            print(f"  [!] Property {p.village} owner wallet '{p.owner_wallet_id}' DOES NOT EXIST in User table!")
            broken_props.append(p)

    # 3. Check Transaction Folios
    folios = TransactionFolio.objects.all()
    for f in folios:
        try:
            buyer = f.buyer
            if not buyer.wallet_address:
                print(f"  [!] Folio {f.id}: Buyer {buyer.email} has no wallet!")
        except User.DoesNotExist:
            print(f"  [!] Folio {f.id}: Buyer does not exist!")

        try:
            seller = f.seller
            if not seller.wallet_address:
                print(f"  [!] Folio {f.id}: Seller {seller.email} has no wallet!")
        except User.DoesNotExist:
            print(f"  [!] Folio {f.id}: Seller does not exist!")

        try:
            notary = f.notary
        except Notary.DoesNotExist:
            print(f"  [!] Folio {f.id}: Notary does not exist!")

    # 4. Check Notaries
    notaries = Notary.objects.all()
    for n in notaries:
        if not n.user:
            print(f"  [!] Notary {n.name} has no User linked!")
        elif not n.user.wallet_address:
            print(f"  [!] Notary {n.name} user {n.user.email} has no wallet!")

if __name__ == "__main__":
    check_integrity()
