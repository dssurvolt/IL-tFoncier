import os
import django
from django.core.files.base import ContentFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from utils.supabase_storage import storage_manager

def test_storage():
    print("🛰️ Tentative de téléversement vers Supabase Storage...")
    dummy_content = b"Contenu de test pour iLot Foncier Storage"
    dummy_file = ContentFile(dummy_content)
    
    url = storage_manager.upload_file(dummy_file, "tests/test_audit.txt")
    
    if url:
        print(f"✅ TEST RÉUSSI ! Le fichier est accessible ici : {url}")
    else:
        print("❌ ÉCHEC DU TEST. Vérifiez les permissions du Bucket 'ilot-media' sur Supabase.")

if __name__ == "__main__":
    test_storage()
