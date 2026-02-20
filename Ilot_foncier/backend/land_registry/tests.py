from django.test import TestCase, Client
from django.urls import reverse
from identity.models import User
from .models import Property
import json

class PropertyAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.wallet = "0x1234567890abcdef1234567890abcdef12345678"
        self.user = User.objects.create_user(wallet_address=self.wallet)
        
    def test_create_property_api(self):
        """Test la création d'une propriété via API."""
        url = reverse('api_property_list')
        data = {
            'owner_wallet': self.wallet,
            'gps_centroid': {'lat': 6.36, 'lng': 2.42},
            'gps_boundaries': [{'lat': 6.36, 'lng': 2.42}, {'lat': 6.37, 'lng': 2.43}]
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json())
        
        # Vérification en base
        prop = Property.objects.first()
        self.assertEqual(prop.owner.wallet_address, self.wallet)
        self.assertEqual(prop.gps_centroid['lat'], 6.36)

    def test_list_properties_api(self):
        """Test le listing des propriétés."""
        Property.objects.create(
            owner=self.user,
            gps_centroid={'lat': 1.0, 'lng': 1.0},
            gps_boundaries=[]
        )
        
        url = reverse('api_property_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['owner'], self.wallet)
