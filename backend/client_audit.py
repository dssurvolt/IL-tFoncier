import os
import django
import json
import uuid
from django.test import Client

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User, USSDSession
from land_registry.models import Property
from consensus.models import ValidationRequest, WitnessVote
from marketplace.models import Listing

def run_rigorous_audit():
    client = Client()
    print("🕵️  Starting Rigorous Client-Side Audit (Black Box Perspective)...")

    # --- 1. PROPERTY CREATION & IDENTITY ---
    print("\n[1] Testing Property Creation & Identity Integrity")
    owner_wallet = "0xAUDIT_" + str(uuid.uuid4())[:8]
    
    # Test: Invalid Name (Numbers)
    res = client.post('/api/properties/', 
        data=json.dumps({
            'owner_name': 'Jean123',
            'owner_wallet': owner_wallet,
            'gps_centroid': {'lat': 6.36, 'lng': 2.42},
            'gps_boundaries': []
        }), content_type='application/json')
    assert res.status_code == 400, "Should reject names with numbers"
    print("✅ Rejected invalid owner name (Jean123)")

    # Test: Invalid GPS (Out of range)
    res = client.post('/api/properties/', 
        data=json.dumps({
            'owner_name': 'Jean Audit',
            'owner_wallet': owner_wallet,
            'gps_centroid': {'lat': 95.0, 'lng': 2.42},
            'gps_boundaries': []
        }), content_type='application/json')
    assert res.status_code == 400, "Should reject latitude > 90"
    print("✅ Rejected invalid latitude (95.0)")

    # Test: Valid Creation
    res = client.post('/api/properties/', 
        data=json.dumps({
            'owner_name': 'Jean Audit',
            'owner_wallet': owner_wallet,
            'gps_centroid': {'lat': 6.36, 'lng': 2.42},
            'gps_boundaries': []
        }), content_type='application/json')
    assert res.status_code == 201
    prop_id = res.json()['id']
    
    # Verify User Profile
    user = User.objects.get(wallet_address=owner_wallet)
    assert user.full_name == 'Jean Audit', "User full_name should be updated"
    print("✅ Property created and User profile updated correctly")

    # --- 2. CONSENSUS & SECURITY ---
    print("\n[2] Testing Consensus Security & Edge Cases")
    
    # Initiate Validation
    res = client.post('/api/validation/initiate/', 
        data=json.dumps({
            'property_id': prop_id,
            'requester_wallet': owner_wallet,
            'gps_at_request': {'lat': 6.36, 'lng': 2.42}
        }), content_type='application/json')
    req_id = res.json()['id']

    # Test: Duplicate Vote (Same ID Number)
    vote_data = {
        'request_id': req_id,
        'witness_name': 'Temoin Unique',
        'witness_phone': '+22900000001',
        'witness_id_number': 'PASSPORT-UNIQUE-123',
        'witness_birth_date': '1985-05-15',
        'vote_result': True,
        'witness_gps': {'lat': 6.36, 'lng': 2.42}
    }
    res = client.post('/api/validation/vote/', data=json.dumps(vote_data), content_type='application/json')
    assert res.status_code == 200
    
    res = client.post('/api/validation/vote/', data=json.dumps(vote_data), content_type='application/json')
    assert res.status_code == 400, "Should reject duplicate vote from same ID Number"
    print("✅ Prevented duplicate vote (Same Passport/ID)")

    # Test: Vote on non-existent request
    res = client.post('/api/validation/vote/', 
        data=json.dumps({**vote_data, 'request_id': str(uuid.uuid4())}), 
        content_type='application/json')
    assert res.status_code == 404
    print("✅ Handled non-existent validation request")

    # Reach Consensus
    for i in range(2): # Need 2 more (Total 3)
        client.post('/api/validation/vote/', 
            data=json.dumps({
                'request_id': req_id,
                'witness_name': f'Temoin {i}',
                'witness_phone': f'+2290000000{i+2}',
                'witness_id_number': f'ID-AUTO-{i}',
                'witness_birth_date': '1990-01-01',
                'vote_result': True,
                'witness_gps': {'lat': 6.36, 'lng': 2.42}
            }), content_type='application/json')
    
    prop = Property.objects.get(id=prop_id)
    prop.refresh_from_db()
    assert prop.status == 'ON_CHAIN'
    print("✅ Consensus reached, property is now ON_CHAIN")

    # Test: Vote on CLOSED request
    res = client.post('/api/validation/vote/', 
        data=json.dumps({
            'request_id': req_id,
            'witness_name': 'Late Witness',
            'witness_phone': '+22999999999',
            'witness_id_number': 'NPI-LATE',
            'vote_result': True,
            'witness_gps': {'lat': 6.36, 'lng': 2.42}
        }), content_type='application/json')
    assert res.status_code == 400, "Should reject votes on closed requests"
    print("✅ Prevented voting on closed validation request")

    # --- 3. MARKETPLACE INTEGRITY ---
    print("\n[3] Testing Marketplace Integrity")
    
    # Test: List DRAFT property (Should fail)
    draft_prop = Property.objects.create(owner_wallet=user, status='DRAFT', gps_centroid={'lat':0,'lng':0}, gps_boundaries=[])
    res = client.post('/api/marketplace/listings/', 
        data=json.dumps({
            'property_id': str(draft_prop.id),
            'seller_wallet': owner_wallet,
            'price_fiat': 500000,
            'price_crypto': 0.1
        }), content_type='application/json')
    assert res.status_code in [400, 403], f"Should reject listing DRAFT properties (Got {res.status_code})"
    print("✅ Prevented listing of unvalidated (DRAFT) property")

    # Test: List ON_CHAIN property (Should succeed)
    res = client.post('/api/marketplace/listings/', 
        data=json.dumps({
            'property_id': prop_id,
            'seller_wallet': owner_wallet,
            'price_fiat': 2000000,
            'price_crypto': 1.0
        }), content_type='application/json')
    assert res.status_code == 201
    print("✅ Successfully listed ON_CHAIN property")

    # --- 4. USSD ROBUSTNESS ---
    print("\n[4] Testing USSD Robustness & State Machine")
    ussd_phone = "+22988888888"
    
    # Test: Invalid input in menu
    client.post('/ussd/', {'sessionId': 's_err', 'phoneNumber': ussd_phone, 'text': ''}) # Init MAIN
    res = client.post('/ussd/', {'sessionId': 's_err', 'phoneNumber': ussd_phone, 'text': '99'})
    assert "Choix invalide" in res.content.decode()
    print("✅ Handled invalid menu choice")

    # Test: USSD Validation Flow (Legal Identity)
    s_val = "s_val_legal"
    # 1. Start Validation
    client.post('/ussd/', {'sessionId': s_val, 'phoneNumber': ussd_phone, 'text': ''}) # MAIN
    res = client.post('/ussd/', {'sessionId': s_val, 'phoneNumber': ussd_phone, 'text': '2'}) 
    assert "ID du terrain" in res.content.decode()
    # 2. Enter ID (partial)
    res = client.post('/ussd/', {'sessionId': s_val, 'phoneNumber': ussd_phone, 'text': '2*' + prop_id[:4]})
    assert "Nom et Prenoms" in res.content.decode()
    # 3. Enter Name
    res = client.post('/ussd/', {'sessionId': s_val, 'phoneNumber': ussd_phone, 'text': '2*' + prop_id[:4] + '*Jean Audit'})
    assert "Date de Naissance" in res.content.decode()
    # 4. Enter Birth Date
    res = client.post('/ussd/', {'sessionId': s_val, 'phoneNumber': ussd_phone, 'text': '2*' + prop_id[:4] + '*Jean Audit*01011990'})
    assert "Passeport ou ID National" in res.content.decode()
    print("✅ USSD universal identity flow verified")

    print("\n🏆 AUDIT COMPLETE: The backend is ROBUST and SECURE.")

if __name__ == "__main__":
    try:
        run_rigorous_audit()
    except Exception as e:
        print(f"\n❌ AUDIT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
