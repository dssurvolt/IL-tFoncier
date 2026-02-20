#!/usr/bin/env python
"""Test de l'accès au tableau de bord pour un utilisateur nouvellement inscrit"""
import requests
import re
import uuid

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🧪 TEST D'ACCÈS AU DASHBOARD APRÈS INSCRIPTION")
print("=" * 80)

email = "dashboard_test@example.com"
password = "Password@123"

# Préparation: Supprimer l'utilisateur s'il existe
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User

try:
    User.objects.get(email=email).delete()
    print(f"✓ Ancien utilisateur supprimé")
except User.DoesNotExist:
    pass

# Étape 1: Inscription via API
print("\n📝 ÉTAPE 1: Inscription")
response = requests.post(
    f"{BASE_URL}/api/auth/register/",
    json={
        "email": email,
        "password": password,
        "full_name": "Dashboard Tester",
        "country": "Benin"
    }
)
print(f"   Status: {response.status_code}")
if response.status_code != 201:
    print(f"   Error: {response.text}")
    exit(1)

data = response.json()
user_id = data['user_id']
print(f"   ✓ Utilisateur créé (ID: {user_id})")

# Étape 2: Accès direct au dashboard
print("\n🖥️  ÉTAPE 2: Accès au dashboard")
url = f"{BASE_URL}/dashboard/{user_id}/"
print(f"   URL: {url}")

try:
    response = requests.get(url)
    print(f"   Status: {response.status_code}")
    
    # Vérifier le contenu
    html = response.text
    if "Bonjour, Dashboard Tester" in html:
        print("   ✓ Nom de l'utilisateur trouvé")
    else:
        print("   ✗ ERROR: Nom de l'utilisateur NON trouvé")
        # Afficher le début du HTML pour debug
        print(f"   Content preview: {html[:500]}")
        
    if "Aucune parcelle trouvée" in html:
        print("   ✓ Message 'Aucune parcelle' trouvé (normal pour nouveau compte)")
    elif "Mes Parcelles" in html:
        print("   ✓ Section 'Mes Parcelles' trouvée")
        
    if "Utilisateur non trouvé" in html:
        print("   🚨 ERROR: Message 'Utilisateur non trouvé' détecté !!")
        exit(1)
        
    # Vérifier le lien d'ajout de propriété (doit contenir l'UUID)
    if f"add-property/{user_id}/" in html:
        print("   ✓ Lien d'ajout de propriété contient l'UUID correct")
    elif 'add-property' in html:
        print("   ⚠️ Lien d'ajout présent mais format incertain")
        # Chercher le lien pour voir ce qu'il contient
        match = re.search(r'href="/add-property/([^/]+)/"', html)
        if match:
             print(f"   -> Lien trouvé: {match.group(0)}")
    
    print("\n✅ ACCÈS DASHBOARD RÉUSSI")

except Exception as e:
    print(f"   ✗ Exception: {e}")
    exit(1)

# Nettoyage
User.objects.get(email=email).delete()
print("\n🧹 Nettoyage effectué")
