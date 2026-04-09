import os
import django
import json
import uuid
from io import BytesIO
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from marketplace.models import Listing, ChatRoom, ChatMessage

def test_chat_features():
    client = Client()
    print("🚀 Testing Chat Features: Emojis & Attachments...")

    # Setup
    seller_email = f"seller_chat_{uuid.uuid4().hex[:4]}@test.com"
    buyer_email = f"buyer_chat_{uuid.uuid4().hex[:4]}@test.com"
    password = "password123"

    seller = User.objects.create_user(email=seller_email, password=password, role=User.Role.USER, full_name="Seller Chat", wallet_address=f"0x{uuid.uuid4().hex[:40]}")
    buyer = User.objects.create_user(email=buyer_email, password=password, role=User.Role.USER, full_name="Buyer Chat", wallet_address=f"0x{uuid.uuid4().hex[:40]}")

    prop = Property.objects.create(
        owner_wallet=seller, 
        village="Chat Village", 
        district="Chat District", 
        status=Property.Status.VALIDATED,
        gps_centroid={"lat": 6.36, "lng": 2.43},
        gps_boundaries=[{"lat": 6.36, "lng": 2.43}, {"lat": 6.37, "lng": 2.43}]
    )
    listing = Listing.objects.create(property=prop, price_fiat=1000000, price_crypto=0.1, status=Listing.Status.ACTIVE)
    room = ChatRoom.objects.create(listing=listing, buyer=buyer, seller=seller)

    client.login(username=buyer_email, password=password)

    # 1. Test Text with Emojis
    emoji_content = "Bonjour 🤝 J'aime cette maison 🏠"
    response = client.post(reverse('api_chat_send'), 
                          data={'room_id': str(room.id), 'content': emoji_content},
                          HTTP_X_CSRFTOKEN='dummy')
    
    assert response.status_code == 201
    data = response.json()
    assert data['content'] == emoji_content
    print("✅ Emoji support verified")

    # 2. Test Attachment
    dummy_file = SimpleUploadedFile("test_doc.pdf", b"dummy content", content_type="application/pdf")
    response = client.post(reverse('api_chat_send'), 
                          data={'room_id': str(room.id), 'content': "Voici le plan", 'attachment': dummy_file},
                          HTTP_X_CSRFTOKEN='dummy')
    
    assert response.status_code == 201
    data = response.json()
    assert 'attachment_url' in data
    assert data['attachment_url'].endswith(".pdf")
    print(f"✅ Attachment support verified: {data['attachment_url']}")

    # 3. Test Attachment Only (No text)
    dummy_img = SimpleUploadedFile("test_img.png", b"fake image content", content_type="image/png")
    response = client.post(reverse('api_chat_send'), 
                          data={'room_id': str(room.id), 'attachment': dummy_img},
                          HTTP_X_CSRFTOKEN='dummy')
    
    assert response.status_code == 201
    data = response.json()
    assert data['content'] == ""
    assert data['attachment_url'].endswith(".png")
    print("✅ Attachment-only message verified")

    print("\n🏁 CHAT FEATURES VERIFIED: Text, Emojis, and Multipose Attachments are working.")

if __name__ == "__main__":
    try:
        test_chat_features()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
