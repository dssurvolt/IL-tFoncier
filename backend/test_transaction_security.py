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

def test_security_constraints():
    client = Client()
    print("🚀 Testing Transaction Security & Access Controls...")

    # 1. Setup Personas
    seller_email = f"seller_s_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_s_{uuid.uuid4().hex[:4]}@simu.com"
    intruder_email = f"intruder_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_s_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    intruder = User.objects.create_user(email=intruder_email, password=password, role=User.Role.USER, full_name="Trudy Intruder", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
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
        village="Village Security",
        district="District Security",
        status=Property.Status.VALIDATED,
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

    # SEC 1: Citizen (Buyer) cannot update transaction steps
    client.login(username=buyer_email, password=password)
    response = client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), {'next_step': 'STEP2_ID_VERIFIED'})
    # Should redirect to somewhere (likely login or dashboard due to notary_required decorator)
    # The notary_required decorator redirects to 'user_dashboard' if not a notary
    assert response.status_code == 302
    folio.refresh_from_db()
    assert folio.status == TransactionFolio.Step.STEP1_NOTARY_SELECTED
    print("✅ Verified: Citizen cannot update transaction status")

    # SEC 2: Intruder cannot view transaction status
    client.logout()
    client.login(username=intruder_email, password=password)
    response = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert response.status_code == 302 # Should redirect to marketplace with error
    print("✅ Verified: Intruder cannot view another's transaction status")

    # SEC 3: Citizen cannot access notary dashboard
    response = client.get(reverse('notary_dashboard'))
    assert response.status_code == 302
    print("✅ Verified: Citizen cannot access notary dashboard")

    print("\n🏁 TRANSACTION SECURITY TESTS PASSED.")

if __name__ == "__main__":
    try:
        test_security_constraints()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
