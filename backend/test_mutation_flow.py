import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from notaries.models import Notary, TransactionFolio
from land_registry.models import Property
from identity.models import User
from notaries.views import web_start_transaction

def test_start_transaction():
    # 1. Setup Data
    buyer, _ = User.objects.get_or_create(
        wallet_address="0xBUYER_TEST_123",
        defaults={'email': 'buyer_unique_test@example.com', 'full_name': 'Buyer Test'}
    )
    
    seller, _ = User.objects.get_or_create(
        wallet_address="0xSELLER_TEST_456",
        defaults={'email': 'seller_unique_test@example.com', 'full_name': 'Seller Test'}
    )
    
    prop, _ = Property.objects.get_or_create(
        owner_wallet=seller,
        gps_centroid={'lat': 6.3, 'lng': 2.4},
        gps_boundaries=[],
        status='ON_CHAIN',
        defaults={'village': 'Test Village', 'district': 'Cotonou'}
    )
    
    notary = Notary.objects.filter(is_verified=True).first()
    if not notary:
        notary = Notary.objects.create(
            name="Notaire Test",
            office_name="Etude Test",
            license_number="TEST-NOT-001",
            email="notaire@test.com",
            phone="12345678",
            address="Rue Test",
            is_verified=True
        )
    
    # 2. Mock Request
    factory = RequestFactory()
    url = f'/transaction/start/{prop.id}/{notary.id}/'
    request = factory.get(url)
    request.user = buyer
    # Add messages middleware mock
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, '_messages', FallbackStorage(request))

    # 3. Call View
    response = web_start_transaction(request, property_id=prop.id, notary_id=notary.id)
    
    print(f"Response status: {response.status_code}")
    print(f"Redirect URL: {response.url}")
    
    # 4. Verify DB
    folio = TransactionFolio.objects.filter(property=prop, buyer=buyer, notary=notary).first()
    if folio:
        print(f"SUCCESS: TransactionFolio created! ID: {folio.id}")
        print(f"Status: {folio.status}")
    else:
        print("FAILURE: TransactionFolio NOT created.")

if __name__ == "__main__":
    test_start_transaction()
