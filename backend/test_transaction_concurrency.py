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
from notaries.models import Notary, TransactionFolio

def test_concurrency():
    client = Client()
    print("🚀 Testing Transaction Concurrency (Blocking Second Buyer)...")

    # Setup
    seller_email = f"seller_c_{uuid.uuid4().hex[:4]}@simu.com"
    buyer1_email = f"buyer1_{uuid.uuid4().hex[:4]}@simu.com"
    buyer2_email = f"buyer2_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_c_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer1 = User.objects.create_user(email=buyer1_email, password=password, role=User.Role.USER, full_name="Buyer One", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer2 = User.objects.create_user(email=buyer2_email, password=password, role=User.Role.USER, full_name="Buyer Two", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Durand", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(user=notary_user, name="Me Durand", office_name="Etude", license_number=f"L-C-{uuid.uuid4().hex[:6]}", email=notary_email, phone="123", address="123", is_verified=True)

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Concurrency",
        district="District Test",
        status=Property.Status.ON_CHAIN,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}]
    )

    # 1. Buyer 1 starts a transaction
    client.login(username=buyer1_email, password=password)
    response = client.get(reverse('web_start_transaction', kwargs={'property_id': str(prop.id), 'notary_id': str(notary.id)}))
    assert response.status_code == 302
    print("✅ Buyer 1 started transaction")

    # 2. Buyer 2 tries to choose a notary for the same property
    client.logout()
    client.login(username=buyer2_email, password=password)
    response = client.get(reverse('web_choose_notary', kwargs={'property_id': str(prop.id)}))
    assert response.status_code == 302
    assert reverse('web_property_detail', kwargs={'pk': str(prop.id)}) in response.url
    print("✅ Verified: Buyer 2 blocked from choosing notary (Property Locked)")

    # 3. Buyer 2 tries to start transaction directly via URL
    response = client.get(reverse('web_start_transaction', kwargs={'property_id': str(prop.id), 'notary_id': str(notary.id)}))
    assert response.status_code == 302
    assert reverse('web_property_detail', kwargs={'pk': str(prop.id)}) in response.url
    print("✅ Verified: Buyer 2 blocked from starting transaction via URL")

    # 4. Buyer 1 is NOT blocked from their own transaction
    client.logout()
    client.login(username=buyer1_email, password=password)
    response = client.get(reverse('web_choose_notary', kwargs={'property_id': str(prop.id)}))
    assert response.status_code == 302
    assert reverse('web_transaction_status', kwargs={'folio_id': str(TransactionFolio.objects.get(buyer=buyer1).id)}) in response.url
    print("✅ Verified: Buyer 1 redirected to their status page")

    print("\n🏁 TRANSACTION CONCURRENCY TESTS PASSED.")

if __name__ == "__main__":
    try:
        test_concurrency()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
