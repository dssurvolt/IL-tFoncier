import os
import django
import json
import uuid
from django.test import Client

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property

def test_duplicate_prevention():
    client = Client()
    print("🛡️ Testing Duplicate Property Prevention...")

    lat, lng = 6.3654, 2.4212
    owner_wallet = "0xUSER_" + str(uuid.uuid4())[:8]

    # 1. Create First Property
    print(f"Registering first property at {lat}, {lng}...")
    res = client.post('/api/properties/', {
        'owner_name': 'Premier Proprietaire',
        'owner_wallet': owner_wallet,
        'gps_centroid': json.dumps({'lat': lat, 'lng': lng}),
        'gps_boundaries': json.dumps([])
    })
    assert res.status_code == 201
    print("✅ First property registered.")

    # 2. Try to register same coordinates (Duplicate)
    print(f"Attempting to register second property at same coordinates...")
    res = client.post('/api/properties/', {
        'owner_name': 'Deuxieme Proprietaire',
        'owner_wallet': '0xOTHER_WALLET',
        'gps_centroid': json.dumps({'lat': lat, 'lng': lng}),
        'gps_boundaries': json.dumps([])
    })
    
    assert res.status_code == 409
    assert "déjà enregistrée" in res.json()['error']
    print("✅ Duplicate registration REJECTED (Status 409).")

    # 3. Try to register very close coordinates
    print(f"Attempting to register property very close (within 0.00005 deg)...")
    res = client.post('/api/properties/', {
        'owner_name': 'Voisin Trop Proche',
        'owner_wallet': '0xVOISIN_WALLET',
        'gps_centroid': json.dumps({'lat': lat + 0.00005, 'lng': lng}),
        'gps_boundaries': json.dumps([])
    })
    assert res.status_code == 409
    print("✅ Near-duplicate registration REJECTED.")

    print("\n✨ DUPLICATE PREVENTION AUDIT PASSED ✨")

if __name__ == "__main__":
    test_duplicate_prevention()
