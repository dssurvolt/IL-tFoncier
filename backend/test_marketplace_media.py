
import os
import django
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property, PropertyMedia
from marketplace.models import Listing

def setup_test_media():
    # 1. Get a listing that is active
    listing = Listing.objects.filter(status='ACTIVE').first()
    if not listing:
        print("No active listing found.")
        return
    
    prop = listing.property
    print(f"Testing for Property: {prop.id}")
    
    # 2. Add media if not present
    if not prop.media.filter(media_type='PHOTO_LAND').exists():
        test_image_source = "/home/st4rk_18/st4rk_18-Projects/Ilot_foncier/titres/Parcelle-a-vendre-a-Calavi-Tankpe-Fifonsi-584x438.webp"
        
        if os.path.exists(test_image_source):
            with open(test_image_source, 'rb') as f:
                media = PropertyMedia.objects.create(
                    property=prop,
                    media_type='PHOTO_LAND',
                    ipfs_cid="test-cid-123"
                )
                media.file.save('test_land.webp', File(f), save=True)
                print(f"Created media: {media.file.url}")
        else:
            print(f"Source image not found: {test_image_source}")
    else:
        print("Media already exists.")
    
    # 3. Test thumbnail_url
    print(f"Thumbnail URL: {prop.thumbnail_url}")
    
    if prop.thumbnail_url:
        print("SUCCESS: thumbnail_url is working!")
    else:
        print("FAILURE: thumbnail_url is None")

if __name__ == "__main__":
    setup_test_media()
