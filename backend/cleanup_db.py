import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import TransactionFolio, Notary
from land_registry.models import Property
from marketplace.models import Listing

def cleanup_all():
    print("🧹 Purge complète des données de test...")
    
    # 1. Supprimer les Folios
    count_folios = TransactionFolio.objects.all().count()
    TransactionFolio.objects.all().delete()
    print(f"✅ {count_folios} folios supprimés.")

    # 2. Supprimer les Annonces
    count_listings = Listing.objects.all().count()
    Listing.objects.all().delete()
    print(f"✅ {count_listings} annonces supprimées.")

    # 3. Supprimer les propriétés de test (sauf Lot 405 si on veut la garder, mais mieux vaut repartir de zéro)
    count_props = Property.objects.all().count()
    Property.objects.all().delete()
    print(f"✅ {count_props} propriétés supprimées.")

    # 4. Nettoyer les Utilisateurs de test (Garder les principaux)
    # On garde Rakib, Ousmane, Akoffodji, Beatrice
    kept_emails = [
        "jp.akoffodji@notariat.bj",
        "ousmane.alfa@exemple.com",
        "admin@ilot.bj"
    ]
    # On va chercher Rakib par son nom car son email change
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if rakib:
        kept_emails.append(rakib.email)
    
    users_to_del = User.objects.exclude(email__in=kept_emails).exclude(is_superuser=True)
    count_users = users_to_del.count()
    users_to_del.delete()
    print(f"✅ {count_users} utilisateurs superflus supprimés.")

    # 5. S'assurer que Me Akoffodji a un seul profil
    Notary.objects.exclude(email="jp.akoffodji@notariat.bj").delete()
    print("✅ Profils notaires nettoyés.")

if __name__ == "__main__":
    cleanup_all()
