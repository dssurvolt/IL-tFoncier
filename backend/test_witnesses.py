
import os
import django
import json
import random
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property, PropertyWitness
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

client = Client()

print("Testing Surveyor & Witnesses Fields...")

# Unique coords
base_lat = 8.123 + random.uniform(0.1, 0.9)
base_lng = 3.456 + random.uniform(0.1, 0.9)

witnesses = [
    {'last_name': 'T1', 'first_name': 'P1', 'birth_date': '1990-01-01', 'gender': 'M', 'phone': '90000001'},
    {'last_name': 'T2', 'first_name': 'P2', 'birth_date': '1992-02-02', 'gender': 'F', 'phone': '90000002'},
    {'last_name': 'T3', 'first_name': 'P3', 'birth_date': '1994-03-03', 'gender': 'M', 'phone': '90000003'},
]

# Create dummy files for ID cards
id_photo_1 = SimpleUploadedFile("id1.jpg", b"fake photo 1 content", content_type="image/jpeg")
id_photo_2 = SimpleUploadedFile("id2.jpg", b"fake photo 2 content", content_type="image/jpeg")
id_photo_3 = SimpleUploadedFile("id3.jpg", b"fake photo 3 content", content_type="image/jpeg")

data = {
    'owner_name': "Witness Tester",
    'birth_date': "1985-05-05",
    'district': "Calavi",
    'village': "Zogbadje",
    'surveyor_name': "Ing. Jean Geometre",
    'area_sqm': "450",
    'area_cadastral': "04a 50ca",
    'gps_centroid': json.dumps({"lat": base_lat, "lng": base_lng}),
    'gps_boundaries': json.dumps([
        {"lat": base_lat, "lng": base_lng}, 
        {"lat": base_lat, "lng": base_lng + 0.001}, 
        {"lat": base_lat + 0.001, "lng": base_lng + 0.001}, 
        {"lat": base_lat + 0.001, "lng": base_lng}
    ]),
    'witnesses': json.dumps(witnesses),
    'witness_id_1': id_photo_1,
    'witness_id_2': id_photo_2,
    'witness_id_3': id_photo_3,
}

response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")
if response.status_code == 201:
    res_data = response.json()
    prop_id = res_data['id']
    prop = Property.objects.get(id=prop_id)
    print(f"SUCCESS: Property created with surveyor: {prop.surveyor_name}")
    
    witness_count = PropertyWitness.objects.filter(property=prop).count()
    print(f"Witnesses count: {witness_count}")
    
    if prop.surveyor_name == "Ing. Jean Geometre" and witness_count == 3:
        print("VERIFIED: Surveyor and Witnesses correctly saved.")
        w1 = PropertyWitness.objects.filter(property=prop, last_name='T1').first()
        if w1 and w1.id_card_photo:
            print(f"Witness 1 ID photo saved: {w1.id_card_photo.name}")
        else:
            print("FAILURE: Witness 1 ID photo missing.")
    else:
        print("FAILURE: Data mismatch.")
else:
    print(f"FAILURE: API Error: {response.content.decode()}")
