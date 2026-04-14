import os
import django
from django.core.files import File
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property, PropertyWitness, PropertyMedia

def prepare_demo():
    print("🚀 Préparation de la démo pour la présentation...")
    
    # 1. Création Admin
    admin, created = User.objects.get_or_create(
        email='admin@ilotfoncier.com',
        defaults={'full_name': 'Administrateur iLôt', 'role': User.Role.ADMIN}
    )
    admin.set_password('admin12345')
    admin.save()
    print(f"✅ Admin créé : {admin.email}")

    # 2. Création Propriété
    prop = Property.objects.create(
        owner_wallet=admin,
        country='Benin',
        village='Abomey-Calavi',
        district='Akassato',
        commune='Abomey-Calavi',
        departement='Atlantique',
        gps_centroid={'lat': 6.446, 'lng': 2.332},
        gps_boundaries=[
            {'lat': 6.446, 'lng': 2.332},
            {'lat': 6.447, 'lng': 2.333},
            {'lat': 6.445, 'lng': 2.334}
        ],
        status=Property.Status.VALIDATED,
        area_sqm=500.0,
        area_cadastral='05a 00ca'
    )
    print(f"✅ Propriété créée : {prop.id}")

    # 3. Ajout des Témoins
    witnesses = [
        {'email': 'sobaberakib4@gmail.com', 'first': 'Jean', 'last': 'Dossou'},
        {'email': 'sobaberakib2@gmail.com', 'first': 'Marie', 'last': 'Soglo'},
        {'email': 'rakib.sobabe@epitech.eu', 'first': 'Rakib', 'last': 'Sobabe'}
    ]
    for w in witnesses:
        PropertyWitness.objects.create(
            property=prop,
            email=w['email'],
            first_name=w['first'],
            last_name=w['last'],
            birth_date=date(1985, 5, 20),
            gender='M',
            phone='+22900000000',
            is_confirmed=True
        )
    print(f"✅ 3 Témoins ajoutés.")

    # 4. Ajout des Documents (depuis la racine)
    docs = [
        ('/home/st4rk_18/IL-tFoncier/certificat_didentification_personnelle.pdf', PropertyMedia.MediaType.LEGAL_DOC),
        ('/home/st4rk_18/IL-tFoncier/images (1).jpeg', PropertyMedia.MediaType.PHOTO_LAND),
        ('/home/st4rk_18/IL-tFoncier/images (2).png', PropertyMedia.MediaType.PHOTO_LAND)
    ]
    
    for path, mtype in docs:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                pm = PropertyMedia(property=prop, media_type=mtype)
                pm.file.save(os.path.basename(path), File(f), save=True)
                print(f"📎 Document attaché : {os.path.basename(path)}")
        else:
            print(f"⚠️ Fichier introuvable : {path}")

    print("🎉 Démo prête ! Bonne présentation !")

if __name__ == "__main__":
    prepare_demo()
