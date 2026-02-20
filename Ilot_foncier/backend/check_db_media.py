
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property, PropertyMedia

print("Listing all Properties and their Media:")
for p in Property.objects.all():
    print(f"Property: {p.id} | Status: {p.status} | Owner: {p.owner_wallet.wallet_address}")
    media = p.media.all()
    print(f"  Media count: {media.count()}")
    for m in media:
        print(f"    - {m.media_type}: {m.ipfs_cid}")
    print("-" * 40)
