import os
import django
import uuid
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import TransactionFolio, Notary

def test_akoffodji_update():
    client = Client()
    print("🚀 Simulating Me AKOFFODJI updating Rakib's Folio...")

    notary_email = "jp.akoffodji@notariat.bj"
    password = "Notaire2026Password"
    
    # Check if user exists
    user = User.objects.filter(email=notary_email).first()
    if not user:
        print("❌ Notary user not found in DB")
        return

    # login
    logged_in = client.login(username=notary_email, password=password)
    if not logged_in:
        print("❌ Login failed for notary")
        return
    print("✅ Notary logged in")

    # Get Rakib's folio
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if not rakib:
        print("❌ Rakib not found")
        return
    
    folio = TransactionFolio.objects.filter(buyer=rakib).first()
    if not folio:
        print("❌ Folio for Rakib not found")
        return
    print(f"✅ Folio found: {folio.id} (Current status: {folio.status})")

    url = reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)})
    
    # Try updating to STEP2
    print(f"POSTing to {url} with next_step=STEP2_ID_VERIFIED")
    response = client.post(url, {'next_step': 'STEP2_ID_VERIFIED'}, follow=True)
    
    if response.status_code == 200:
        print("✅ Response 200 (Followed redirect)")
        # Check messages in response
        messages = list(response.context.get('messages', []))
        for m in messages:
            print(f"Message: {m}")
        
        folio.refresh_from_db()
        print(f"New Status: {folio.status}")
        if folio.status == 'STEP2_ID_VERIFIED':
            print("✅ Status successfully updated to STEP2")
        else:
            print("❌ Status NOT updated!")
    else:
        print(f"❌ POST failed with status {response.status_code}")
        # print(response.content.decode())

if __name__ == "__main__":
    test_akoffodji_update()
