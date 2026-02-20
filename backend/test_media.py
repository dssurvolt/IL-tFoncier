import os
import django
import json
import uuid
from django.test import Client
from io import BytesIO

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property, PropertyMedia

def test_media_upload():
    client = Client()
    print("📸 Testing Media Upload & DISPUTED Status...")

    owner_wallet = "0xMEDIA_" + str(uuid.uuid4())[:8]
    
    # 1. Create Property with Files
    # Simulate a file
    photo = BytesIO(b"fake photo content")
    photo.name = 'terrain.jpg'
    
    doc = BytesIO(b"fake pdf content")
    doc.name = 'titre.pdf'

    print("Creating property with 2 files...")
    res = client.post('/api/properties/', {
        'owner_name': 'Jean Media',
        'owner_wallet': owner_wallet,
        'gps_centroid': json.dumps({'lat': 6.36, 'lng': 2.42}),
        'gps_boundaries': json.dumps([]),
        'files': [photo, doc]
    })
    
    assert res.status_code == 201
    prop_id = res.json()['id']
    print(f"✅ Property created: {prop_id}")

    # 2. Verify Media in DB
    media_count = PropertyMedia.objects.filter(property_id=prop_id).count()
    print(f"Media count in DB: {media_count}")
    assert media_count == 2
    
    # Check types
    photo_media = PropertyMedia.objects.get(property_id=prop_id, media_type='PHOTO_LAND')
    doc_media = PropertyMedia.objects.get(property_id=prop_id, media_type='LEGAL_DOC')
    print(f"✅ Media types verified: {photo_media.media_type}, {doc_media.media_type}")
    assert photo_media.ipfs_cid.startswith('Qm')

    # 3. Test DISPUTED Status
    print("Testing DISPUTED status...")
    prop = Property.objects.get(id=prop_id)
    prop.status = Property.Status.DISPUTED
    prop.save()
    
    # Verify via API
    res = client.get('/api/properties/')
    props = res.json()['results']
    target = next(p for p in props if p['id'] == prop_id)
    assert target['status'] == 'DISPUTED'
    assert target['media_count'] == 2
    print("✅ DISPUTED status and media count verified via API")

    print("\n✨ MEDIA & DISPUTED AUDIT PASSED ✨")

if __name__ == "__main__":
    test_media_upload()
