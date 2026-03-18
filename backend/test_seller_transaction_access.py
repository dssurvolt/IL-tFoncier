import os
import django
import uuid
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from marketplace.models import Listing, Notification
from notaries.models import Notary, TransactionFolio

def test_seller_flow():
    client = Client()
    print("🚀 Testing Seller-side Transaction Access & Notifications...")

    # 1. Setup Personas
    seller_email = f"seller_t_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_t_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_t_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Durand", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(
        user=notary_user,
        name="Me Durand",
        office_name="Étude Durand",
        license_number=f"LIC-{uuid.uuid4().hex[:6]}",
        email=notary_email,
        phone="+22901020304",
        address="123 Rue du Commerce, Cotonou",
        is_verified=True
    )

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Seller",
        district="District Seller",
        status=Property.Status.ON_CHAIN,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}]
    )

    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )

    # 2. Notary updates transaction to STEP2
    client.login(username=notary_email, password=password)
    client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), {'next_step': 'STEP2_ID_VERIFIED'})
    print("✅ Notary updated to STEP2")

    # 3. Seller logs in and checks notifications
    client.logout()
    client.login(username=seller_email, password=password)
    
    # Check if notification exists
    notifs = Notification.objects.filter(user_wallet=seller, type='TRANSACTION_UPDATE')
    assert notifs.count() == 1
    print(f"✅ Seller received In-App Notification: {notifs.first().payload['title']}")

    # 4. Seller accesses transaction status page
    response = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert response.status_code == 200
    assert "Identités Vérifiées" in response.content.decode()
    print("✅ Seller successfully accessed transaction status page")

    # 5. Check if notification is marked as read after visiting the page
    notifs = Notification.objects.filter(user_wallet=seller, type='TRANSACTION_UPDATE', read_at__isnull=False)
    assert notifs.count() == 1
    print("✅ Seller notification marked as read after visiting status page")

    # 6. Verify My Transactions page for seller
    response = client.get(reverse('user_transactions'))
    assert response.status_code == 200
    assert "Village Seller" in response.content.decode()
    print("✅ Seller 'My Transactions' page shows the sale")

    print("\n🏁 SELLER-SIDE TRANSACTION TESTS PASSED.")

if __name__ == "__main__":
    try:
        test_seller_flow()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
