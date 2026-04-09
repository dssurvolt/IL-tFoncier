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

def test_listing_availability_flow():
    client = Client()
    print("🚀 Testing Listing Availability & Contract Status Flow...")

    # setup
    seller_email = f"seller_av_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_av_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_av_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Jean", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(user=notary_user, name="Me Jean", office_name="Etude", license_number=f"L-AV-{uuid.uuid4().hex[:6]}", email=notary_email, phone="123", address="123", is_verified=True)

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Availability",
        district="District Test",
        status=Property.Status.VALIDATED,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}]
    )

    listing = Listing.objects.create(property=prop, price_fiat=1000, price_crypto=0.01, status=Listing.Status.ACTIVE)

    # 1. Initial State: Available
    assert not listing.is_under_contract
    print("✅ Initial State: Listing is Available")

    # 2. Transaction Started: marked as Under Contract
    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )
    assert listing.is_under_contract
    print("✅ Transaction Started: Listing is marked as Under Contract")

    # 3. Transaction Cancelled (Dispute/Quiproquo): Should become available again
    client.login(username=notary_email, password=password)
    client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), {'next_step': 'CANCELLED'})
    
    folio.refresh_from_db()
    assert folio.status == 'CANCELLED'
    assert not listing.is_under_contract
    print("✅ Transaction Cancelled: Listing is available again")

    # 4. New Transaction Started
    folio2 = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )
    assert listing.is_under_contract
    print("✅ New Transaction Started: Listing is Under Contract again")

    # 5. Transaction Completed: Listing should be marked as SOLD (and thus disappear from ACTIVE filter)
    client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio2.id)}), {'next_step': 'STEP6_COMPLETED'})
    
    listing.refresh_from_db()
    assert listing.status == Listing.Status.SOLD
    # Since status is SOLD, it is no longer ACTIVE. 
    # web_marketplace filters by status=ACTIVE and witness_count > 0.
    print("✅ Transaction Completed: Listing status is now SOLD")

    print("\n🏁 LISTING AVAILABILITY FLOW TEST PASSED.")

if __name__ == "__main__":
    try:
        test_listing_availability_flow()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
