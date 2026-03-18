import os
import django
import json
import uuid
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property, PropertyWitness
from marketplace.models import Listing, ChatRoom, ChatMessage
from notaries.models import Notary, TransactionFolio

def run_simulation():
    client = Client()
    print("🚀 Starting Global Marketplace & Transaction Simulation...")

    # 1. Setup Personas
    seller_email = f"seller_{uuid.uuid4().hex[:4]}@simu.com"
    buyer_email = f"buyer_{uuid.uuid4().hex[:4]}@simu.com"
    notary_email = f"notary_{uuid.uuid4().hex[:4]}@simu.com"
    password = "password123"

    seller_wallet = f"0x{uuid.uuid4().hex[:40]}"
    buyer_wallet = f"0x{uuid.uuid4().hex[:40]}"
    notary_wallet = f"0x{uuid.uuid4().hex[:40]}"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="John Seller", wallet_address=seller_wallet)
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Bob Buyer", wallet_address=buyer_wallet)
    notary_user = User.objects.create_user(email=notary_email, password=password, role=User.Role.NOTARY, full_name="Me Durand", wallet_address=notary_wallet)

    notary = Notary.objects.create(
        user=notary_user,
        name="Me Durand",
        office_name="Étude Durand",
        license_number=f"LIC-{uuid.uuid4().hex[:6]}",
        email=notary_email,
        phone="+22901020304",
        address="123 Rue du Commerce, Cotonou",
        is_verified=True
    )
    print(f"✅ Personas created with wallets: Seller({seller_wallet}), Buyer({buyer_wallet})")

    # 2. Property Creation & Certification (Prerequisite for Listing)
    prop = Property.objects.create(
        owner_wallet=seller,
        village="Village Test",
        district="District Test",
        status=Property.Status.ON_CHAIN, # Force on-chain for listing
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}, {"lat": 6.37, "lng": 2.44}]
    )
    # Add a witness (Required rule)
    PropertyWitness.objects.create(
        property=prop, 
        last_name="Témoin", 
        first_name="Un", 
        email="w1@test.com",
        birth_date="1990-01-01",
        gender="M",
        phone="+22900000001"
    )
    print(f"✅ Property created and certified: {prop.id}")

    # 3. Create Marketplace Listing
    listing = Listing.objects.create(
        property=prop,
        price_fiat=5000000,
        price_crypto=0.5,
        status=Listing.Status.ACTIVE
    )
    print(f"✅ Listing created: {listing.id} for {listing.price_fiat} FCFA")

    # 4. Simulation: Buyer browses Marketplace
    client.login(username=buyer_email, password=password)
    response = client.get(reverse('web_marketplace'))
    assert response.status_code == 200
    assert "Village Test" in response.content.decode()
    print("✅ Marketplace browsing successful")

    # 5. Simulation: Buyer starts Chat
    response = client.get(reverse('web_start_chat', kwargs={'listing_id': str(listing.id)}))
    assert response.status_code == 302 # Redirect to chat room
    room = ChatRoom.objects.get(buyer=buyer, listing=listing)
    print(f"✅ ChatRoom initiated: {room.id}")

    # Buyer sends a message
    response = client.post(reverse('api_chat_send'), 
                          data=json.dumps({
                              'room_id': str(room.id),
                              'content': "Hello, is this still available?"
                          }),
                          content_type='application/json',
                          HTTP_X_CSRFTOKEN='dummy')
    assert response.status_code == 201
    print("✅ Buyer message sent")

    # Verify Notification for Seller
    client.logout()
    client.login(username=seller_email, password=password)
    response = client.get(reverse('api_unread_notifications_count'))
    assert response.status_code == 200
    assert response.json()['count'] >= 1
    print(f"✅ Seller notification received: {response.json()['count']} unread")

    # 6. Simulation: Notary Selection & Transaction Initiation
    # Buyer selects the notary
    client.login(username=buyer_email, password=password)
    response = client.get(reverse('web_start_transaction', kwargs={
        'property_id': str(prop.id),
        'notary_id': str(notary.id)
    }))
    assert response.status_code == 302 # Redirect to status page
    folio = TransactionFolio.objects.get(property=prop, buyer=buyer)
    print(f"✅ Transaction Folio created: {folio.id} at Step 1")

    # 7. Simulation: Notary processes the transaction
    client.logout()
    client.login(username=notary_email, password=password)
    
    # Verify Notary UI Isolation (Should NOT see Citizen links)
    response = client.get(reverse('notary_dashboard'))
    content = response.content.decode()
    assert "Gestion des Folios" in content
    assert "Mon Patrimoine" not in content
    assert "🛒 Marketplace" not in content
    assert "🔔" not in content
    print("✅ Notary UI Isolation verified (No citizen links or notifications)")

    # Verify Notary Redirection from Citizen Dashboard
    response = client.get(reverse('user_dashboard', kwargs={'wallet': str(notary_user.id)}))
    assert response.status_code == 302
    assert reverse('notary_dashboard') in response.url
    print("✅ Notary redirection from citizen dashboard verified")

    steps_to_validate = [
        ('STEP2_ID_VERIFIED', "Identities Verified"),
        ('STEP3_DEED_SIGNED', "Deed Signed"),
        ('STEP4_ANDF_DEPOSITED', "ANDF Deposited"),
        ('STEP5_TITLE_MODIFIED', "Title Modified"),
        ('STEP6_COMPLETED', "Completed")
    ]

    for step, label in steps_to_validate:
        post_data = {'next_step': step}
        if step == 'STEP4_ANDF_DEPOSITED':
            post_data['andf_number'] = "ANDF-12345"
            
        response = client.post(reverse('update_transaction_step', kwargs={'folio_id': str(folio.id)}), data=post_data)
        assert response.status_code == 302
        folio.refresh_from_db()
        assert folio.status == step
        print(f"✅ Notary validated: {label}")

    # 8. Simulation: Check Final Status (as Buyer)
    client.logout()
    client.login(username=buyer_email, password=password)
    response = client.get(reverse('web_transaction_status', kwargs={'folio_id': str(folio.id)}))
    assert response.status_code == 200
    assert "Titre Récupéré" in response.content.decode()
    print("✅ Buyer sees Completed Transaction")

    # 8.1 Simulation: Self-Purchase Prevention
    client.logout()
    client.login(username=seller_email, password=password)
    # The owner tries to start a transaction on their own property
    response = client.get(reverse('web_start_transaction', kwargs={
        'property_id': str(prop.id),
        'notary_id': str(notary.id)
    }))
    assert response.status_code == 302
    assert reverse('web_property_detail', kwargs={'pk': str(prop.id)}) in response.url
    print("✅ Self-purchase prevention verified (Redirection to property detail)")

    # 9. Simulation: Marketplace Inquiry (PMF Metric)
    response = client.post(reverse('api_marketplace_inquire'),
                          data=json.dumps({
                              'listing_id': str(listing.id),
                              'user_id': str(buyer.id)
                          }),
                          content_type='application/json')
    assert response.status_code == 201
    print("✅ Marketplace Inquiry recorded")

    # 10. Simulation: Admin checks PMF Dashboard
    client.logout()
    admin_email = f"admin_{uuid.uuid4().hex[:4]}@simu.com"
    admin_user = User.objects.create_superuser(email=admin_email, password=password)
    client.login(username=admin_email, password=password)
    response = client.get(reverse('pmf_dashboard'))
    assert response.status_code == 200
    assert "Monthly Cohort Dashboard" in response.content.decode()
    print("✅ PMF Dashboard functional")

    print("\n🏁 ALL SYSTEMS FUNCTIONAL: Marketplace, Chat, Notary Value Chain, and PMF Metrics verified.")

if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        print(f"❌ Simulation FAILED: {e}")
        import traceback
        traceback.print_exc()
