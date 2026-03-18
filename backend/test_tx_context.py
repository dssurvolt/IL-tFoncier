import os
import django
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

def test_transactions_context():
    print("🚦 Test du contexte de 'Mes Transactions' pour Rakib...")
    client = Client()
    
    # Login Rakib
    email = "rakib.sobabe@ilot.bj"
    password = "Rakib2026Password"
    logged_in = client.login(username=email, password=password)
    print(f"🔑 Login status: {logged_in}")
    
    url = reverse('user_transactions')
    response = client.get(url)
    print(f"📡 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        # Check context
        ctx = response.context
        print(f"🛡️ Context is_notary: {ctx.get('is_notary')}")
        print(f"👤 User Role in Context: {ctx.get('user').role}")
        
        # Check template used
        templates = [t.name for t in response.templates]
        print(f"📄 Templates: {templates}")
        
    print("\n✅ Test terminé.")

if __name__ == "__main__":
    test_transactions_context()
