
import os
import django
import json
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from django.test import Client

client = Client()

# Test with 5 points (Pentagon)
data = {
    'owner_name': "Pentagon Tester",
    'birth_date': "1990-01-01",
    'gps_centroid': json.dumps({"lat": 6.5, "lng": 2.5}),
    'gps_boundaries': json.dumps([
        {"lat": 6.5, "lng": 2.5}, 
        {"lat": 6.5, "lng": 2.51}, 
        {"lat": 6.51, "lng": 2.52}, 
        {"lat": 6.52, "lng": 2.51},
        {"lat": 6.51, "lng": 2.5}
    ]),
}

print("Testing Variable Boundaries (5 points)...")
response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")
if response.status_code == 201:
    res_data = response.json()
    prop_id = res_data['id']
    prop = Property.objects.get(id=prop_id)
    print(f"SUCCESS: Property created with {len(prop.gps_boundaries)} points.")
    if len(prop.gps_boundaries) == 5:
        print("Verified: 5 points recorded correctly.")
    else:
        print(f"FAILURE: Expected 5 points, got {len(prop.gps_boundaries)}")
else:
    print(f"FAILURE: API Error: {response.content.decode()}")
