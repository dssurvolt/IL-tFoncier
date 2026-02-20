import os
import django
import json
import uuid
from django.test import Client
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User, USSDSession
from land_registry.models import Property
from consensus.models import ValidationRequest, WitnessVote
from marketplace.models import Listing

def test_full_backend_cycle():
    client = Client()
    print("🚀 Starting Comprehensive Backend Audit...")

    # 1. Identity & Property Creation
    print("\n--- Testing Property Creation ---")
    owner_wallet = "0xOWNER_" + str(uuid.uuid4())[:8]
    res = client.post('/api/properties/', 
        data=json.dumps({
            'owner_name': 'Jean.D-Almeida',
            'owner_wallet': owner_wallet,
            'gps_centroid': {'lat': 6.36, 'lng': 2.42},
            'gps_boundaries': [{'lat': 6.36, 'lng': 2.42}, {'lat': 6.37, 'lng': 2.43}]
        }), 
        content_type='application/json'
    )
    assert res.status_code == 201, f"Failed to create property: {res.content}"
    prop_id = res.json()['id']
    print(f"✅ Property created: {prop_id}")

    # 2. Consensus Flow
    print("\n--- Testing Consensus Flow ---")
    # Initiate
    print("Initiating validation...")
    res = client.post('/api/validation/initiate/', 
        data=json.dumps({
            'property_id': prop_id,
            'requester_wallet': owner_wallet,
            'gps_at_request': {'lat': 6.36, 'lng': 2.42}
        }), 
        content_type='application/json'
    )
    if res.status_code != 201:
        print(f"❌ Initiation failed: {res.status_code}")
        print(res.content.decode()[:500])
        return
    req_id = res.json()['id']
    print(f"✅ Validation initiated: {req_id}")

    # Voting (Need 3 votes for consensus)
    for i in range(3):
        witness_name = f"Temoin Numero {i}"
        witness_phone = f"+2299700000{i}"
        witness_id_number = f"DOC-ID-123456789{i}"
        witness_birth_date = "1990-01-01"
        
        print(f"Voting as {witness_name}...")
        res = client.post('/api/validation/vote/', 
            data=json.dumps({
                'request_id': req_id,
                'witness_name': witness_name,
                'witness_phone': witness_phone,
                'witness_id_number': witness_id_number,
                'witness_birth_date': witness_birth_date,
                'vote_result': True,
                'witness_gps': {'lat': 6.36, 'lng': 2.42}
            }),
            content_type='application/json'
        )
        if res.status_code != 200:
            print(f"❌ Vote {i} failed: {res.status_code}")
            print(res.content.decode()[:500])
            return
        print(f"✅ Vote {i} recorded: {res.json()['consensus']}")

    # Check Property Status (Should be ON_CHAIN now)
    prop = Property.objects.get(id=prop_id)
    print(f"📊 Property Status after 3 votes: {prop.status}")
    assert prop.status == Property.Status.ON_CHAIN, "Property should be ON_CHAIN after consensus"

    # 3. Marketplace
    print("\n--- Testing Marketplace ---")
    # Success case
    res = client.post('/api/marketplace/listings/', 
        data=json.dumps({
            'property_id': prop_id,
            'seller_wallet': owner_wallet,
            'price_fiat': 1000000,
            'price_crypto': 0.5
        }), 
        content_type='application/json'
    )
    assert res.status_code == 201, f"Marketplace listing failed: {res.content}"
    print(f"✅ Marketplace listing created: {res.json()['id']}")

    # Failure case: Not the owner
    res = client.post('/api/marketplace/listings/', 
        data=json.dumps({
            'property_id': prop_id,
            'seller_wallet': "0xHACKER",
            'price_fiat': 10,
            'price_crypto': 0.1
        }), 
        content_type='application/json'
    )
    assert res.status_code == 403, "Marketplace should block non-owners"
    print("✅ Marketplace security (Owner check) verified")

    # 4. USSD Flow
    print("\n--- Testing USSD Flow ---")
    phone = "+22990000000"
    session_id = "sess_audit_" + str(uuid.uuid4())[:8]
    
    # Step 1: Main Menu
    res = client.post('/ussd/', {'sessionId': session_id, 'phoneNumber': phone, 'text': ''})
    assert "CON" in res.content.decode(), "USSD Main menu failed"
    
    # Step 2: Choose Registration (1)
    res = client.post('/ussd/', {'sessionId': session_id, 'phoneNumber': phone, 'text': '1'})
    assert "Nom et Prenom" in res.content.decode(), "USSD Reg step 1 failed"
    
    # Step 3: Enter Name
    res = client.post('/ussd/', {'sessionId': session_id, 'phoneNumber': phone, 'text': '1*Jean.D-Almeida'})
    assert "Latitude" in res.content.decode(), "USSD Reg step 2 failed"
    
    # Step 4: Enter Latitude
    res = client.post('/ussd/', {'sessionId': session_id, 'phoneNumber': phone, 'text': '1*Jean.D-Almeida*6.35'})
    assert "Longitude" in res.content.decode(), "USSD Reg step 3 failed"
    
    # Step 5: Enter Longitude
    res = client.post('/ussd/', {'sessionId': session_id, 'phoneNumber': phone, 'text': '1*Jean.D-Almeida*6.35*2.40'})
    assert "superficie" in res.content.decode(), "USSD Reg step 4 failed"

    # --- Validation Tests ---
    print("\n--- Testing USSD Compliance & Validation ---")
    
    # Test 1: Invalid Name (Numbers)
    s1 = "sess_val_1"
    client.post('/ussd/', {'sessionId': s1, 'phoneNumber': phone, 'text': ''}) # MAIN
    client.post('/ussd/', {'sessionId': s1, 'phoneNumber': phone, 'text': '1'}) # -> REG_ASK_NAME
    res = client.post('/ussd/', {'sessionId': s1, 'phoneNumber': phone, 'text': '1*Jean123'})
    assert "Nom invalide" in res.content.decode(), "Should reject numeric names"
    print("✅ Name validation (no numbers) verified")
    
    # Test 2: Invalid Latitude
    s2 = "sess_val_2"
    client.post('/ussd/', {'sessionId': s2, 'phoneNumber': phone, 'text': ''}) # MAIN
    client.post('/ussd/', {'sessionId': s2, 'phoneNumber': phone, 'text': '1'}) # -> REG_ASK_NAME
    client.post('/ussd/', {'sessionId': s2, 'phoneNumber': phone, 'text': '1*Jean.D'}) # -> REG_ASK_LAT
    res = client.post('/ussd/', {'sessionId': s2, 'phoneNumber': phone, 'text': '1*Jean.D*150'})
    assert "Latitude invalide" in res.content.decode(), "Should reject latitude > 90"
    print("✅ Latitude range validation verified")
    
    # Test 3: Invalid Longitude
    s3 = "sess_val_3"
    client.post('/ussd/', {'sessionId': s3, 'phoneNumber': phone, 'text': ''}) # MAIN
    client.post('/ussd/', {'sessionId': s3, 'phoneNumber': phone, 'text': '1'}) # -> REG_ASK_NAME
    client.post('/ussd/', {'sessionId': s3, 'phoneNumber': phone, 'text': '1*Jean.D'}) # -> REG_ASK_LAT
    client.post('/ussd/', {'sessionId': s3, 'phoneNumber': phone, 'text': '1*Jean.D*6.35'}) # -> REG_ASK_LNG
    res = client.post('/ussd/', {'sessionId': s3, 'phoneNumber': phone, 'text': '1*Jean.D*6.35*300'})
    assert "Longitude invalide" in res.content.decode(), "Should reject longitude > 180"
    print("✅ Longitude range validation verified")

    print("\n✨ ALL BACKEND AUDITS PASSED CLEANLY ✨")

if __name__ == "__main__":
    try:
        test_full_backend_cycle()
    except Exception as e:
        print(f"\n💥 AUDIT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
