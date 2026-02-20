
import os
import django
import json
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property, PropertyMedia
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

# 1. Setup User
wallet = "0xMediaFinalTest"
user, _ = User.objects.get_or_create(wallet_address=wallet.lower(), full_name="Final Media Tester")

client = Client()

gps_centroid = {"lat": 40.0, "lng": 40.0}
gps_boundaries = [{"lat": 40.0, "lng": 40.0}, {"lat": 40.0, "lng": 40.01}, {"lat": 40.01, "lng": 40.01}, {"lat": 40.01, "lng": 40.0}]

# Upload a real-ish file
file_content = b"this is a test image content"
file1 = SimpleUploadedFile("my_land.jpg", file_content, content_type="image/jpeg")

data = {
    'owner_wallet': wallet,
    'owner_name': "Final Media Tester",
    'gps_centroid': json.dumps(gps_centroid),
    'gps_boundaries': json.dumps(gps_boundaries),
    'files': [file1]
}

print("Posting data with file...")
response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")

if response.status_code == 201:
    prop_id = response.json()['id']
    prop = Property.objects.get(id=prop_id)
    m = prop.media.first()
    print(f"Property created: {prop.id}")
    if m and m.file:
        print(f"SUCCESS: File saved locally at {m.file.path}")
        print(f"CID generated: {m.ipfs_cid}")
        # Verify file existance
        if os.path.exists(m.file.path):
            print("Verified: File exists on disk.")
        else:
             print("FAILURE: File does NOT exist on disk.")
    else:
        print("FAILURE: Media or file field is missing.")
else:
    print(f"FAILURE: API Error: {response.content.decode()}")
