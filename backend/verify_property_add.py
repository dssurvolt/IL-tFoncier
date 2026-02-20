
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from django.test import Client

# 1. Setup User
wallet = "0xTestWalletForAddProp"
user, _ = User.objects.get_or_create(wallet_address=wallet.lower(), full_name="Test User")
print(f"User created/found: {user.wallet_address}")

# 2. Simulate POST to PropertyListAPI
client = Client()

# Valid Convex Polygon around Paris (just for test)
# Centroid: 48.8566, 2.3522
# Points forming a square around it
gps_centroid = {"lat": 48.8566, "lng": 2.3522}
gps_boundaries = [
    {"lat": 48.8570, "lng": 2.3520},
    {"lat": 48.8570, "lng": 2.3530},
    {"lat": 48.8560, "lng": 2.3530},
    {"lat": 48.8560, "lng": 2.3520}
]

data = {
    'owner_wallet': wallet, # Mixed case to test normalization
    'owner_name': "Test User",
    'gps_centroid': json.dumps(gps_centroid),
    'gps_boundaries': json.dumps(gps_boundaries),
}

print("Posting data...")
response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")
print(f"Response Content: {response.content.decode()}")

if response.status_code == 201:
    print("Property created via API.")
    
    # 3. Verify in DB
    props = Property.objects.filter(owner_wallet__wallet_address=wallet.lower())
    print(f"Properties found for user: {props.count()}")
    for p in props:
        print(f" - {p.id} Status: {p.status}")
else:
    print("Failed to create property.")

