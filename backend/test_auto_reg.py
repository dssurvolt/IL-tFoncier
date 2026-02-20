
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

# Test Auto-Registration Flow
# No wallet provided, but birth_date is provided
data = {
    'owner_name': "Marcel Koulibaly",
    'birth_date': "1985-05-12",
    'gps_centroid': json.dumps({"lat": 6.4, "lng": 2.4}),
    'gps_boundaries': json.dumps([
        {"lat": 6.4, "lng": 2.4}, 
        {"lat": 6.4, "lng": 2.41}, 
        {"lat": 6.41, "lng": 2.41}, 
        {"lat": 6.41, "lng": 2.4}
    ]),
}

print("Testing Auto-Registration with Birth Date...")
response = client.post('/api/properties/', data)

print(f"Response Status: {response.status_code}")
if response.status_code == 201:
    res_data = response.json()
    generated_wallet = res_data['wallet_address']
    prop_id = res_data['id']
    
    print(f"Generated Wallet: {generated_wallet}")
    print(f"Property ID: {prop_id}")
    
    # Verify User
    user = User.objects.get(wallet_address=generated_wallet)
    print(f"Verified User in DB: {user.full_name}, Birth: {user.birth_date}")
    
    # Verify Property
    prop = Property.objects.get(id=prop_id)
    print(f"Verified Property in DB: OnChainID={prop.on_chain_id}")
    
    if prop.on_chain_id:
        print("SUCCESS: Automatic identifiers generated for User and Parcel.")
    else:
        print("FAILURE: OnChainID not generated.")
else:
    print(f"FAILURE: API Error: {response.content.decode()}")
