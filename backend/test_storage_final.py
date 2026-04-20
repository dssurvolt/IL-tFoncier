import os
import django
from django.core.files.base import ContentFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from utils.supabase_storage import storage_manager

def test_storage():
    print("🛰️ Tentative de téléversement d'une image de test...")
    # Une image PNG minimale de 1x1 pixel
    dummy_img = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdcG\xe1\x02\x00\x00\x00\x00IEND\xaeB`\x82'
    dummy_file = ContentFile(dummy_img)
    
    # On utilise une extension .png pour satisfaire les règles du Bucket
    url = storage_manager.upload_file(dummy_file, "tests/audit_success.png")
    
    if url:
        print(f"✅ TEST RÉUSSI ! Votre configuration est parfaite.")
        print(f"🔗 Image stockée ici : {url}")
    else:
        print("❌ ÉCHEC DU TEST. Vérifiez encore les réglages du Bucket.")

if __name__ == "__main__":
    test_storage()
