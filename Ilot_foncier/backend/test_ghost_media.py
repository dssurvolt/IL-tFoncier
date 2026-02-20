
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
wallet = "0xGhostTest"
user, _ = User.objects.get_or_create(wallet_address=wallet.lower(), full_name="Ghost Tester")

client = Client()

gps_centroid = {"lat": 30.0, "lng": 30.0}
gps_boundaries = [{"lat": 30.0, "lng": 30.0}, {"lat": 30.0, "lng": 30.01}, {"lat": 30.01, "lng": 30.01}, {"lat": 30.01, "lng": 30.0}]

# Test Case 1: No files
data_empty = {
    'owner_wallet': wallet,
    'owner_name': "Ghost Tester",
    'gps_centroid': json.dumps(gps_centroid),
    'gps_boundaries': json.dumps(gps_boundaries),
}

print("Testing with NO files...")
res1 = client.post('/api/properties/', data_empty)
if res1.status_code == 201:
    p = Property.objects.get(id=res1.json()['id'])
    print(f"Property created, media count: {p.media.count()}")
    if p.media.count() == 0:
        print("SUCCESS: No media created for empty files list.")
    else:
        print("FAILURE: Ghost media created!")

# Test Case 2: 1 file
file1 = SimpleUploadedFile("test.png", b"test_content", content_type="image/png")
data_files = {
    'owner_wallet': wallet,
    'owner_name': "Ghost Tester",
    'gps_centroid': json.dumps({"lat": 31.0, "lng": 31.0}),
    'gps_boundaries': json.dumps([{"lat": 31.0, "lng": 31.0}, {"lat": 31.0, "lng": 31.01}, {"lat": 31.01, "lng": 31.01}, {"lat": 31.01, "lng": 31.0}]),
    'files': [file1]
}

print("\nTesting with 1 file...")
res2 = client.post('/api/properties/', data_files)
if res2.status_code == 201:
    p = Property.objects.get(id=res2.json()['id'])
    print(f"Property created, media count: {p.media.count()}")
    if p.media.count() == 1:
        print("SUCCESS: 1 media created correctly.")
    else:
        print("FAILURE: Media count mismatch.")
