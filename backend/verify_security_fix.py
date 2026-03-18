import os
import django
import json
from django.test import Client
from django.urls import reverse
from identity.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verify_fix():
    c = Client()
    
    # 1. Créer deux utilisateurs
    u1 = User.objects.create_user(email="user1@ilot.bj", password="Password123!", full_name=None)
    u2 = User.objects.create_user(email="user2@ilot.bj", password="Password123!", full_name="User Two")
    
    # 2. Login en tant que User 1
    c.login(email="user1@ilot.bj", password="Password123!")
    
    # 3. Tenter d'accéder au dashboard de User 2
    u2_dashboard_url = reverse('user_dashboard', kwargs={'wallet': str(u2.id)})
    response = c.get(u2_dashboard_url, follow=True)
    
    # Vérifier la redirection
    print(f"URL finale après tentative d'accès à autrui: {response.request['PATH_INFO']}")
    if str(u1.id) in response.request['PATH_INFO']:
        print("✅ SÉCURITÉ : Redirigé avec succès vers son propre dashboard.")
    else:
        print("❌ ÉCHEC : La faille d'accès direct est toujours présente.")
        
    # 4. Vérifier le rendu "None" pour User 1 (qui a full_name=None)
    content = response.content.decode('utf-8')
    if "Bonjour, user1@ilot.bj" in content:
        print("✅ RENDU : Le fallback sur l'email fonctionne (pas de 'None').")
    elif "Bonjour, None" in content:
        print("❌ RENDU : 'Bonjour, None' détecté.")
    else:
        print("⚠️ RENDU : Impossible de vérifier le texte de bienvenue.")

if __name__ == '__main__':
    verify_fix()
