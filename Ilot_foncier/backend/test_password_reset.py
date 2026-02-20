#!/usr/bin/env python
"""Test complet du système de réinitialisation de mot de passe"""
import requests
import json
import re
import time

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("🔐 TESTS DU SYSTÈME DE RÉINITIALISATION DE MOT DE PASSE")
print("=" * 70)

# Créer un utilisateur de test
print("\n📝 Préparation: Création d'un utilisateur de test")
test_email = "reset_test@example.com"
test_password = "OldPassword@123"

# Supprimer l'utilisateur s'il existe
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User, PasswordResetToken

try:
    user = User.objects.get(email=test_email)
    user.delete()
    print(f"   ✓ Ancien utilisateur supprimé")
except User.DoesNotExist:
    pass

# Créer le nouvel utilisateur
user = User.objects.create_user(
    email=test_email,
    password=test_password,
    full_name="Test Reset User",
    country="Benin"
)
print(f"   ✓ Utilisateur créé: {test_email}")
print(f"   ✓ Mot de passe initial: {test_password}")

# Test 1: Demande de réinitialisation avec email valide
print("\n🧪 Test 1: Demande de réinitialisation avec email valide")
response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={"email": test_email}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "La demande devrait réussir"
print("   ✓ PASS")

# Récupérer le token depuis la base de données
time.sleep(0.5)
reset_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at')
token = reset_token.token
print(f"   📧 Token généré: {token[:20]}...")

# Test 2: Demande de réinitialisation avec email inexistant
print("\n🧪 Test 2: Demande avec email inexistant (ne révèle pas l'existence)")
response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={"email": "nonexistent@example.com"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "Devrait retourner succès (sécurité)"
print("   ✓ PASS - Ne révèle pas si l'email existe")

# Test 3: Demande sans email
print("\n🧪 Test 3: Demande sans email")
response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 400, "Devrait échouer"
print("   ✓ PASS")

# Test 4: Réinitialisation avec token valide et mot de passe fort
print("\n🧪 Test 4: Réinitialisation avec token valide")
new_password = "NewPassword@456"
response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": token,
        "new_password": new_password
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "La réinitialisation devrait réussir"
print("   ✓ PASS")

# Test 5: Vérifier que l'ancien mot de passe ne fonctionne plus
print("\n🧪 Test 5: Ancien mot de passe ne fonctionne plus")
response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": test_password
    }
)
print(f"   Status: {response.status_code}")
assert response.status_code == 401, "L'ancien mot de passe devrait être rejeté"
print("   ✓ PASS - Ancien mot de passe rejeté")

# Test 6: Vérifier que le nouveau mot de passe fonctionne
print("\n🧪 Test 6: Nouveau mot de passe fonctionne")
response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": new_password
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "Le nouveau mot de passe devrait fonctionner"
print("   ✓ PASS - Nouveau mot de passe accepté")

# Test 7: Réutilisation du même token (devrait échouer)
print("\n🧪 Test 7: Réutilisation du token (devrait échouer)")
response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": token,
        "new_password": "AnotherPassword@789"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 400, "Le token déjà utilisé devrait être rejeté"
print("   ✓ PASS - Token déjà utilisé rejeté")

# Test 8: Token invalide
print("\n🧪 Test 8: Token invalide")
response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": "invalid_token_12345",
        "new_password": "Password@123"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 400, "Token invalide devrait être rejeté"
print("   ✓ PASS")

# Test 9: Mot de passe faible lors de la réinitialisation
print("\n🧪 Test 9: Mot de passe faible lors de la réinitialisation")
# Créer un nouveau token
response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={"email": test_email}
)
time.sleep(0.5)
new_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at').token

response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": new_token,
        "new_password": "weak"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 400, "Mot de passe faible devrait être rejeté"
print("   ✓ PASS - Mot de passe faible rejeté")

# Test 10: Vérifier l'expiration du token (simulation)
print("\n🧪 Test 10: Vérification de l'expiration du token")
from django.utils import timezone
from datetime import timedelta

# Créer un token expiré manuellement
expired_token = PasswordResetToken.objects.create(
    user=user,
    token="expired_token_test",
    expires_at=timezone.now() - timedelta(hours=2)
)

response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": "expired_token_test",
        "new_password": "ValidPassword@123"
    }
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 400, "Token expiré devrait être rejeté"
assert "expiré" in response.json()['error'].lower()
print("   ✓ PASS - Token expiré rejeté")

# Test 11: Plusieurs demandes successives (seul le dernier token devrait fonctionner)
print("\n🧪 Test 11: Plusieurs demandes successives")
# Première demande
requests.post(f"{BASE_URL}/api/password-reset/request/", json={"email": test_email})
time.sleep(0.3)
first_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at').token

# Deuxième demande
requests.post(f"{BASE_URL}/api/password-reset/request/", json={"email": test_email})
time.sleep(0.3)
second_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at').token

print(f"   Premier token: {first_token[:20]}...")
print(f"   Second token: {second_token[:20]}...")

# Utiliser le second token
response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": second_token,
        "new_password": "FinalPassword@999"
    }
)
print(f"   Status avec second token: {response.status_code}")
assert response.status_code == 200, "Le second token devrait fonctionner"

# Le premier token devrait être invalidé
response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": first_token,
        "new_password": "AnotherPassword@888"
    }
)
print(f"   Status avec premier token: {response.status_code}")
assert response.status_code == 400, "Le premier token devrait être invalidé"
print("   ✓ PASS - Anciens tokens invalidés après réinitialisation")

print("\n" + "=" * 70)
print("✅ TOUS LES TESTS SONT PASSÉS! (11/11)")
print("=" * 70)

# Nettoyage
print("\n🧹 Nettoyage...")
user.delete()
print("   ✓ Utilisateur de test supprimé")
