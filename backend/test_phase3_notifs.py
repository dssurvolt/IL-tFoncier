import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from notaries.models import Notary, TransactionFolio
from marketplace.models import Notification
from notaries.utils import notify_transaction_update

def test_notifications():
    # 1. Setup entities
    buyer = User.objects.filter(email="buyer@test.com").first()
    if not buyer:
        buyer = User.objects.create_user(email="buyer@test.com", password="password123", full_name="Acheteur Test")
    
    seller = User.objects.filter(email="seller@test.com").first()
    if not seller:
        seller = User.objects.create_user(email="seller@test.com", password="password123", full_name="Vendeur Test")

    prop = Property.objects.first()
    notary = Notary.objects.first()

    # 2. Create a folio
    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP4_ANDF_DEPOSITED,
        andf_dossier_number="ANDF-2026-TEST-99"
    )
    
    # 3. Trigger notification
    print(f"Triggering notification for Folio: {folio.id} at step: {folio.get_status_display()}")
    notify_transaction_update(folio)

    # 4. Verify in database
    buyer_notifs = Notification.objects.filter(user_wallet=buyer, type='TRANSACTION_UPDATE').order_by('-created_at')
    if buyer_notifs.exists():
        last_notif = buyer_notifs.first()
        print(f"✅ Notification created for Buyer: {last_notif.payload['title']}")
        print(f"Message: {last_notif.payload['message']}")
    else:
        print("❌ Notification NOT created for Buyer")

    seller_notifs = Notification.objects.filter(user_wallet=seller, type='TRANSACTION_UPDATE').order_by('-created_at')
    if seller_notifs.exists():
        print(f"✅ Notification created for Seller: {seller_notifs.first().payload['title']}")
    else:
        print("❌ Notification NOT created for Seller")

if __name__ == "__main__":
    test_notifications()
