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

def test_notary_as_client_prevention():
    client = Client()
    print("🚀 Testing Prevention of Notary as Client...")

    # 1. Setup Personas
    seller_email = f"seller_p_{uuid.uuid4().hex[:4]}@simu.com"
    notary_buyer_email = f"notary_b_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_p_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_buyer_user = User.objects.create_user(email=notary_buyer_email, password=password, role=User.Role.NOTARY, full_name="Me Durand Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Official", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(
        user=notary_user,
        name="Me Official",
        office_name="Étude Durand",
        license_number=f"LIC-{uuid.uuid4().hex[:6]}",
        email=notary_email,
        phone="+22901020304",
        address="123 Rue du Commerce, Cotonou",
        is_verified=True
    )

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Role Test",
        district="District Role Test",
        status=Property.Status.ON_CHAIN,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}]
    )

    # SEC: Notary account cannot choose a notary to buy land
    client.login(username=notary_buyer_email, password=password)
    response = client.get(reverse('web_choose_notary', kwargs={'property_id': str(prop.id)}))
    assert response.status_code == 302
    assert reverse('web_property_detail', kwargs={'pk': str(prop.id)}) in response.url
    print("✅ Verified: Notary account blocked from choosing a notary (buying)")

    # SEC: Notary account cannot start a transaction directly
    response = client.get(reverse('web_start_transaction', kwargs={'property_id': str(prop.id), 'notary_id': str(notary.id)}))
    assert response.status_code == 302
    assert reverse('web_property_detail', kwargs={'pk': str(prop.id)}) in response.url
    print("✅ Verified: Notary account blocked from starting a transaction")

    print("\n🏁 NOTARY-CLIENT PREVENTION TEST PASSED.")

def test_synchronous_status():
    client = Client()
    print("🚀 Testing Synchronous Transaction Status (Buyer & Seller)...")

    # Setup
    seller_email = f"seller_sync_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_sync_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_sync_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Durand", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    notary = Notary.objects.create(user=notary_user, name="Me Durand", office_name="Etude", license_number=f"L-{uuid.uuid4().hex[:6]}", email=notary_email, phone="123", address="123", is_verified=True)

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Sync",
        district="District Sync",
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

    # 1. Check Initial Status for both
    client.login(username=buyer_email, password=password)
    resp_buyer = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert str(TransactionFolio.Step.STEP1_NOTARY_SELECTED.label) in resp_buyer.content.decode()

    client.logout()
    client.login(username=seller_email, password=password)
    resp_seller = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert str(TransactionFolio.Step.STEP1_NOTARY_SELECTED.label) in resp_seller.content.decode()
    print("✅ Initial status is identical for Buyer and Seller")

    # 2. Notary updates to STEP2
    client.logout()
    client.login(username=notary_email, password=password)
    client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), {'next_step': 'STEP2_ID_VERIFIED'})
    print("✅ Notary updated to STEP2")

    # 3. Check Updated Status for both
    client.logout()
    client.login(username=buyer_email, password=password)
    resp_buyer = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert str(TransactionFolio.Step.STEP2_ID_VERIFIED.label) in resp_buyer.content.decode()

    client.logout()
    client.login(username=seller_email, password=password)
    resp_seller = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert str(TransactionFolio.Step.STEP2_ID_VERIFIED.label) in resp_seller.content.decode()
    print("✅ Updated status (STEP2) is identical for Buyer and Seller")

    print("\n🏁 SYNCHRONOUS STATUS TEST PASSED.")

if __name__ == "__main__":
    try:
        test_notary_as_client_prevention()
        test_synchronous_status()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
