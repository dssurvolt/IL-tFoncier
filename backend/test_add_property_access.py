#!/usr/bin/env python
"""Test de l'accès à la page d'ajout de propriété avec un UUID"""
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🧪 TEST D'ACCÈS À LA PAGE ADD PROPERTY")
print("=" * 80)

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User

# Créer un utilisateur temporaire
email = "addprop_test@example.com"
password = "Password@123"

try:
    User.objects.get(email=email).delete()
except User.DoesNotExist:
    pass

user = User.objects.create_user(
    email=email,
    password=password,
    full_name="Add Property Tester",
    country="Benin"
)
print(f"✓ Utilisateur créé (ID: {user.id})")

# Tester l'accès avec UUID
url = f"{BASE_URL}/add-property/{user.id}/"
print(f"\n🔗 Accès à: {url}")

response = requests.get(url)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    print("   ✓ Page accessible")
    if "Déclarer une Nouvelle Parcelle" in response.text or "Ajouter" in response.text: # Vérifier titre
         print("   ✓ Contenu correct (titre trouvé)")
    else:
         print("   ⚠️ Titre non trouvé, vérification du contenu...")
         # print(response.text[:200])
elif response.status_code == 302:
    print(f"   ⚠️ Redirection vers: {response.headers.get('Location')}")
    if 'login' in response.headers.get('Location', ''):
        print("   -> Redirection vers login (normal si user not found)")
        print("   🚨 MAIS l'utilisateur DEVRAIT être trouvé via UUID!")
        exit(1)
else:
    print(f"   ✗ Erreur inattendue")
    exit(1)

print("\nTo test with non-existent UUID:")
fake_uuid = uuid.uuid4()
url_fake = f"{BASE_URL}/add-property/{fake_uuid}/"
response = requests.get(url_fake)
print(f"   Accès à {url_fake} -> Status: {response.status_code}")
if response.status_code == 302:
    print("   ✓ Redirection vers login (correct pour utilisateur inconnu)")
else:
    print(f"   ⚠️ Comportement inattendu: {response.status_code}")

# Nettoyage
user.delete()
print("\n🧹 Nettoyage effectué")
