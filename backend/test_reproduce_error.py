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

def test_reproduce_notary_error():
    client = Client()
    print("🚀 Attempting to reproduce Notary Update Error...")

    # Data setup
    notary_email = f"notary_{uuid.uuid4().hex[:4]}@ilot.bj"
    password = "password123"
    
    notary_user = User.objects.create_user(
        email=notary_email, 
        password=password, 
        role=User.Role.NOTARY, 
        full_name="Me Reproduce"
    )
    notary = Notary.objects.create(
        user=notary_user, 
        name="Me Reproduce", 
        office_name="Etude", 
        license_number=f"L-REP-{uuid.uuid4().hex[:6]}", 
        email=notary_email, 
        phone="123", 
        address="123", 
        is_verified=True
    )

    seller = User.objects.create_user(email=f"seller_{uuid.uuid4().hex[:4]}@ilot.bj", password=password)
    buyer = User.objects.create_user(email=f"buyer_{uuid.uuid4().hex[:4]}@ilot.bj", password=password)

    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Reproduce",
        district="District",
        status=Property.Status.VALIDATED,
        gps_centroid={"lat": 1, "lng": 1},
        gps_boundaries=[{"lat": 1, "lng": 1}]
    )

    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=buyer,
        seller=seller,
        notary=notary,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )

    # login as notary
    client.login(username=notary_email, password=password)
    
    # Try to update to STEP2
    print(f"DEBUG: Folio ID = {folio.id}")
    url = reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)})
    print(f"DEBUG: URL = {url}")
    
    response = client.post(url, {'next_step': 'STEP2_ID_VERIFIED'})
    
    if response.status_code != 302:
        print(f"❌ Error detected! Status code: {response.status_code}")
        if hasattr(response, 'context') and response.context and 'error' in response.context:
             print(f"Error Context: {response.context['error']}")
        # print(response.content.decode())
    else:
        print("✅ No error in step 2 (from STEP1 to STEP2)")

    # Try to update to STEP4 (ANDF) with andf_number
    response = client.post(url, {
        'next_step': 'STEP4_ANDF_DEPOSITED',
        'andf_number': 'ANDF-2026-TEST'
    })
    
    if response.status_code != 302:
        print(f"❌ Error detected in STEP4! Status code: {response.status_code}")
    else:
        folio.refresh_from_db()
        print(f"✅ STEP4 Update success. ANDF Number: {folio.andf_dossier_number}")

    # Check for notary dashboard access
    resp_dash = client.get(reverse('notary_dashboard'))
    if resp_dash.status_code != 200:
        print(f"❌ Error accessing dashboard! Status: {resp_dash.status_code}")
    else:
        print("✅ Dashboard access success")

if __name__ == "__main__":
    test_reproduce_notary_error()
