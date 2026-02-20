
import os
import django
import json
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property
from django.test import Client

client = Client()

print("Testing Area & Administrative Fields (Unique Coords)...")

# Randomizing coords slightly to avoid 409
base_lat = 7.123 + random.uniform(0.1, 0.9)
base_lng = 2.456 + random.uniform(0.1, 0.9)

data = {
    'owner_name': "Superficie Tester Unique",
    'birth_date': "1988-08-08",
    'district': "Porto-Novo",
    'village': "Avakpa",
    'area_sqm': "1250",
    'area_cadastral': "12a 50ca",
    'gps_centroid': json.dumps({"lat": base_lat, "lng": base_lng}),
    'gps_boundaries': json.dumps([
        {"lat": base_lat, "lng": base_lng}, 
        {"lat": base_lat, "lng": base_lng + 0.001}, 
        {"lat": base_lat + 0.001, "lng": base_lng + 0.001}, 
        {"lat": base_lat + 0.001, "lng": base_lng}
    ]),
}

response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")
if response.status_code == 201:
    res_data = response.json()
    prop_id = res_data['id']
    prop = Property.objects.get(id=prop_id)
    print(f"SUCCESS: Property created.")
    print(f"District: {prop.district}")
    print(f"Area Metric: {prop.area_sqm} m2")
    print(f"Area Cadastral: {prop.area_cadastral}")
    
    if prop.district == "Porto-Novo" and float(prop.area_sqm) == 1250.0:
        print("VERIFIED: Data correctly saved.")
    else:
        print(f"FAILURE: Data mismatch. Got {prop.district} and {prop.area_sqm}")
else:
    print(f"FAILURE: API Error: {response.content.decode()}")
