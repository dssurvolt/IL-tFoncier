import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import TransactionFolio, Notary
from land_registry.models import Property
from django.utils import timezone

def try_update_rakib_folio():
    print("🚀 Trying to update Rakib's Folio...")
    
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if not rakib:
        print("❌ Rakib not found")
        return

    akoffodji_user = User.objects.filter(full_name="Me Jean-Pierre AKOFFODJI").first()
    if not akoffodji_user:
        print("❌ Akoffodji not found")
        return
    
    folio = TransactionFolio.objects.filter(buyer=rakib).first()
    if not folio:
        print("❌ Folio not found")
        return

    print(f"Current Status: {folio.status}")
    
    # Simulate update_transaction_step logic
    try:
        next_step = TransactionFolio.Step.STEP2_ID_VERIFIED
        folio.status = next_step
        folio.step2_verified_at = timezone.now()
        folio.save()
        print(f"✅ Step 2 update success.")
        
        # Try to go to step 6
        print("Trying Step 6 (Final Transfer)...")
        folio.status = TransactionFolio.Step.STEP6_COMPLETED
        folio.step6_completed_at = timezone.now()
        
        # Mutation Cadastre logic
        prop = folio.property
        print(f"Prop owner before: {prop.owner_wallet.email} ({prop.owner_wallet.wallet_address})")
        print(f"Buyer: {folio.buyer.email} ({folio.buyer.wallet_address})")
        
        prop.owner_wallet = folio.buyer
        prop.save()
        print("✅ Property owner updated in DB.")
        
        folio.save()
        print("✅ Folio step 6 saved.")
        
    except Exception as e:
        print(f"❌ CRASH during update: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try_update_rakib_folio()
