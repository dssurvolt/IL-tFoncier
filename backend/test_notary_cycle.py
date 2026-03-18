import os
import django
import uuid
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from notaries.models import Notary, TransactionFolio

def test_full_update_cycle():
    client = Client()
    print("🚀 Testing Full Notary Update Cycle...")

    # Data setup
    notary_email = "jp.akoffodji@notariat.bj"
    password = "Notaire2026Password"
    
    # 1. Login
    logged_in = client.login(username=notary_email, password=password)
    if not logged_in:
        print("❌ Login FAILED")
        return

    # 2. Get the folio for Rakib
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    folio = TransactionFolio.objects.filter(buyer=rakib).first()
    
    if not folio:
        print("❌ Folio not found")
        return
        
    # Reset status if it was completed
    if folio.status == 'STEP6_COMPLETED' or folio.status == 'CANCELLED':
        print(f"Resetting folio {folio.id} to STEP1 for testing...")
        folio.status = 'STEP1_NOTARY_SELECTED'
        folio.save()

    url = reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)})

    # Test STEP 2
    print("Testing update to STEP2...")
    response = client.post(url, {'next_step': 'STEP2_ID_VERIFIED'})
    if response.status_code != 302:
        print(f"❌ STEP2 FAILED - Status: {response.status_code}")
        # print(response.content.decode()) # This might be long
    else:
        print("✅ STEP2 Success")

    # Test STEP 4 (Requires ANDF number)
    print("Testing update to STEP4...")
    response = client.post(url, {
        'next_step': 'STEP4_ANDF_DEPOSITED',
        'andf_number': 'TEST-ANDF-001'
    })
    if response.status_code != 302:
        print(f"❌ STEP4 FAILED - Status: {response.status_code}")
    else:
        print("✅ STEP4 Success")

    # Test STEP 6 (Final transfer)
    print("Testing update to STEP6...")
    response = client.post(url, {'next_step': 'STEP6_COMPLETED'})
    if response.status_code != 302:
        print(f"❌ STEP6 FAILED - Status: {response.status_code}")
    else:
        print("✅ STEP6 Success")

    print("\n🏁 TEST CYCLE COMPLETED.")

if __name__ == "__main__":
    try:
        test_full_update_cycle()
    except Exception as e:
        print(f"❌ CRASH: {e}")
        import traceback
        traceback.print_exc()
