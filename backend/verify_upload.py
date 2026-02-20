
import os
import django
import json
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

# 1. Setup User
wallet = "0xMediaTestWallet"
user, _ = User.objects.get_or_create(wallet_address=wallet.lower(), full_name="Media Tester")

# 2. Simulate POST with Files
client = Client()

gps_centroid = {"lat": 20.0, "lng": 20.0}
gps_boundaries = [{"lat": 20.0, "lng": 20.0}, {"lat": 20.0, "lng": 20.01}, {"lat": 20.01, "lng": 20.01}, {"lat": 20.01, "lng": 20.0}]

# Create dummy files
file1 = SimpleUploadedFile("photo1.jpg", b"fake_image_content", content_type="image/jpeg")
file2 = SimpleUploadedFile("doc.pdf", b"fake_pdf_content", content_type="application/pdf")

data = {
    'owner_wallet': wallet,
    'owner_name': "Media Tester",
    'gps_centroid': json.dumps(gps_centroid),
    'gps_boundaries': json.dumps(gps_boundaries),
    'files': [file1, file2] # Client.post handles list of files for multipart
}

print("Posting data with files...")
response = client.post('/api/properties/', data) # content_type is automatic for multipart

print(f"Response Status: {response.status_code}")
print(f"Response Content: {response.content.decode()}")

if response.status_code == 201:
    prop_id = response.json()['id']
    prop = Property.objects.get(id=prop_id)
    media_count = prop.media.count()
    print(f"Property created: {prop.id}")
    print(f"Media count: {media_count}")
    for m in prop.media.all():
        print(f" - Media: {m.media_type} (CID: {m.ipfs_cid})")
        
    if media_count == 2:
        print("SUCCESS: 2 files uploaded and saved.")
    else:
        print("FAILURE: Media count mismatch.")
else:
    print("FAILURE: API Request failed.")
