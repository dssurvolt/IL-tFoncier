import os
import django
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

def reproduce_sidebar_bug():
    print("🚦 Reproduction du bug de la barre latérale pour Rakib...")
    client = Client()
    
    # Login Rakib
    email = "rakib.sobabe@ilot.bj"
    password = "Rakib2026Password"
    client.login(username=email, password=password)
    
    # Visiter 'Mes Transactions'
    url = reverse('user_transactions')
    response = client.get(url)
    
    content = response.content.decode()
    
    # Vérifier l'affichage de "Espace Notaire"
    has_notary_space = "Espace Notaire" in content
    has_citoyen_space = "Mon Patrimoine" in content
    
    print(f"🧐 'Espace Notaire' présent dans le code : {has_notary_space}")
    print(f"🧐 'Mon Patrimoine' présent dans le code : {has_citoyen_space}")
    
    if has_notary_space and not has_citoyen_space:
        print("🚨 BUG REPRODUIT : Rakib voit la barre latérale Notaire !")
    elif has_citoyen_space and not has_notary_space:
        print("✅ COMPORTEMENT CORRECT : Rakib voit sa propre barre latérale.")
    else:
        print("❓ État hybride ou inattendu.")

if __name__ == "__main__":
    reproduce_sidebar_bug()
