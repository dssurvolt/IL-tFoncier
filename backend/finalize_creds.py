import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.models import Notary

def finalize_and_check():
    print("🚀 Finalisation des identifiants acteurs...")
    
    # 1. RAKIB
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if rakib:
        # On uniformise son email pour éviter les trucs complexes
        rakib.email = "rakib.sobabe@ilot.bj"
        rakib.set_password("Rakib2026Password")
        rakib.save()
        print(f"✅ RAKIB : {rakib.email} / Rakib2026Password")

    # 2. AKOFFODJI
    ak_user = User.objects.filter(email="jp.akoffodji@notariat.bj").first()
    if not ak_user: # S'il a été renommé ou autre
        ak_user = User.objects.filter(full_name="Me Jean-Pierre AKOFFODJI").first()
    
    if ak_user:
        ak_user.email = "jp.akoffodji@notariat.bj"
        ak_user.set_password("Notaire2026Password")
        ak_user.save()
        print(f"✅ NOTAIRE : {ak_user.email} / Notaire2026Password")
        
        # S'assurer que le profil est ok
        Notary.objects.get_or_create(
            user=ak_user,
            defaults={
                'name': "Jean-Pierre AKOFFODJI",
                'office_name': "Étude de Maître AKOFFODJI",
                'email': ak_user.email
            }
        )

    # 3. OUSMANE
    ousmane = User.objects.filter(email="ousmane.alfa@exemple.com").first()
    if ousmane:
        ousmane.set_password("Ousmane2026Password")
        ousmane.save()
        print(f"✅ VENDEUR : {ousmane.email} / Ousmane2026Password")

if __name__ == "__main__":
    finalize_and_check()
