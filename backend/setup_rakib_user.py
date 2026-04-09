import os
import django
import uuid
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property, AuthorizedSurveyor
from marketplace.models import Listing

def run():
    # 1. Create User
    email = "sobaberakib2@gmail.com"
    password = "RobustPassword2026!#"
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name="Rakib Sobabe",
            role=User.Role.USER,
            is_active=True
        )
        print(f"User {email} created.")
    else:
        user = User.objects.get(email=email)
        print(f"User {email} already exists.")

    # 2. Create an Authorized Surveyor if none exists
    surveyor, _ = AuthorizedSurveyor.objects.get_or_create(
        license_number="BEN-SURV-2026-001",
        defaults={
            "name": "Jean-Pierre Agon",
            "email": "jp.agon@geometre.bj",
            "phone": "+229 97 00 11 22",
            "is_active": True
        }
    )

    # 3. Create Property 1
    p1 = Property.objects.create(
        owner_wallet=user,
        country="Benin",
        departement="Atlantique",
        commune="Abomey-Calavi",
        district="Godomey",
        village="Togoudo",
        surveyor=surveyor,
        area_sqm=500.0,
        area_cadastral="05a 00ca",
        gps_centroid={"lat": 6.3941, "lng": 2.3418},
        gps_boundaries=[
            {"lat": 6.3942, "lng": 2.3417},
            {"lat": 6.3942, "lng": 2.3419},
            {"lat": 6.3940, "lng": 2.3419},
            {"lat": 6.3940, "lng": 2.3417}
        ],
        status=Property.Status.VALIDATED
    )
    print(f"Property 1 created: {p1.id}")

    # 4. Create Listing 1
    l1 = Listing.objects.create(
        property=p1,
        listing_type="SALE",
        price_fiat=15000000,
        is_negotiable=True,
        description="Magnifique terrain de 500m² à Togoudo, idéal pour résidence principale. Proche du goudron.",
        status=Listing.Status.ACTIVE
    )
    print(f"Listing 1 created: {l1.id}")

    # 5. Create Property 2
    p2 = Property.objects.create(
        owner_wallet=user,
        country="Benin",
        departement="Littoral",
        commune="Cotonou",
        district="12ème Arrondissement",
        village="Fidjrossè",
        surveyor=surveyor,
        area_sqm=350.0,
        area_cadastral="03a 50ca",
        gps_centroid={"lat": 6.3547, "lng": 2.3683},
        gps_boundaries=[
            {"lat": 6.3548, "lng": 2.3682},
            {"lat": 6.3548, "lng": 2.3684},
            {"lat": 6.3546, "lng": 2.3684},
            {"lat": 6.3546, "lng": 2.3682}
        ],
        status=Property.Status.VALIDATED
    )
    print(f"Property 2 created: {p2.id}")

    # 6. Create Listing 2
    l2 = Listing.objects.create(
        property=p2,
        listing_type="SALE",
        price_fiat=25000000,
        is_negotiable=False,
        description="Terrain titré à Fidjrossè Plage. Emplacement stratégique pour projet hôtelier ou villa de luxe.",
        status=Listing.Status.ACTIVE
    )
    print(f"Listing 2 created: {l2.id}")

if __name__ == "__main__":
    run()
