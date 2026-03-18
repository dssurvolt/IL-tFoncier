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
from marketplace.models import Listing
from notaries.models import Notary, TransactionFolio

def test_transfer():
    client = Client()
    print("🚀 Testing Automatic Ownership Transfer & Listing Closure...")

    # Setup
    seller_email = f"seller_o_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_o_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_o_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Durand", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(user=notary_user, name="Me Durand", office_name="Etude", license_number=f"L-{uuid.uuid4().hex[:6]}", email=notary_email, phone="123", address="123")

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Transfer",
        district="District Test",
        status=Property.Status.ON_CHAIN,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}]
    )

    listing = Listing.objects.create(property=prop, price_fiat=1000, price_crypto=0.01, status=Listing.Status.ACTIVE)

    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )

    # Notary completes the transaction
    client.login(username=notary_email, password=password)
    response = client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), {'next_step': 'STEP6_COMPLETED'})
    assert response.status_code == 302

    # Verification 1: Ownership transfer
    prop.refresh_from_db()
    assert prop.owner_wallet == buyer
    print("✅ Verified: Property ownership transferred to buyer")

    # Verification 2: Listing Closure
    listing.refresh_from_db()
    assert listing.status == Listing.Status.SOLD
    print("✅ Verified: Listing marked as SOLD")

    print("\n🏁 OWNERSHIP TRANSFER TEST PASSED.")

if __name__ == "__main__":
    try:
        test_transfer()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
