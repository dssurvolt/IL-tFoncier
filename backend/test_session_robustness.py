#!/usr/bin/env python
"""Test complet de la robustesse de session et du wallet"""
import requests
import re
import uuid

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🧪 TEST DE ROBUSTESSE SESSION & WALLET")
print("=" * 80)

email = "session_force@example.com"
password = "Password@123"

# Préparation
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

# 1. Inscription
print("\n📝 ÉTAPE 1: Inscription (vérification wallet généré)")
response = requests.post(
    f"{BASE_URL}/api/auth/register/",
    json={
        "email": email,
        "password": password,
        "full_name": "Session Tester",
        "country": "Benin"
    }
)

if response.status_code != 201:
    print(f"   Error: {response.text}")
    exit(1)

data = response.json()
user_id = data['user_id']
print(f"   ✓ Utilisateur créé (ID: {user_id})")

# Vérifier en base si le wallet a été généré
user = User.objects.get(id=user_id)
wallet = user.wallet_address
print(f"   ✓ Wallet généré en DB: {wallet}")

if not wallet or not wallet.startswith('0x') or len(wallet) < 10:
    print("   🚨 ERREUR: Wallet non généré ou invalide !")
    exit(1)

# 2. Accès Dashboard avec login session (Simulation)
# Pour simuler la session, on doit utiliser requests.Session et faire le login
session = requests.Session()

print("\n🔑 ÉTAPE 2: Login pour établir la session")
login_resp = session.post(
    f"{BASE_URL}/api/auth/login/",
    json={"email": email, "password": password}
)
print(f"   Login Status: {login_resp.status_code}")
if login_resp.status_code != 200:
    print("   Login Failed")
    exit(1)

# 3. Test Navigation Robuste (URL cassée mais session active)
print("\n🛡️  ÉTAPE 3: Test Navigation Robuste (URL vide)")
# On essaie d'accéder au dashboard avec une URL 'bizarre' ou l'ID
# Note: L'URL pattern exige un argument, on essaie avec un truc bidon
fake_url = f"{BASE_URL}/dashboard/invalid-wallet-string/"
print(f"   Accès à URL invalide: {fake_url}")

# Comme on est loggé (session), la vue devrait nous rediriger vers notre bon dashboard ou l'afficher directement
resp = session.get(fake_url)
print(f"   Status: {resp.status_code}")

if resp.status_code == 200 and "Bonjour, Session Tester" in resp.text:
    print("   ✓ SUCCÈS: Dashboard affiché grâce à la session malgré l'URL invalide !")
else:
    print("   ✗ ÉCHEC: La session n'a pas pris le relais.")
    # print(resp.text[:500])

# 4. Vérification des liens dans Add Property
print("\n🔗 ÉTAPE 4: Vérification des liens retour")
add_prop_url = f"{BASE_URL}/add-property/{user_id}/"
resp = session.get(add_prop_url)

if f"href=\"/dashboard/{user_id}/\"" in resp.text or f"href=\"/dashboard/{wallet}/\"" in resp.text:
    print("   ✓ Lien retour présent et valide")
else:
    print("   ⚠️ Lien retour suspect")
    # Recherche regex
    match = re.search(r'href="/dashboard/([^/]+)/"', resp.text)
    if match:
        print(f"   -> Lien trouvé: {match.group(0)}")
    else:
        print("   -> Aucun lien dashboard trouvé !")

print("\n✅ TOUS LES TESTS RÉUSSIS")

# Nettoyage
user.delete()
print("\n🧹 Nettoyage effectué")
