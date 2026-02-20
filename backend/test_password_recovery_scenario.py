#!/usr/bin/env python
"""Test d'intégration complète du parcours de récupération de mot de passe"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🎭 SCÉNARIO COMPLET: UTILISATEUR PERD SON MOT DE PASSE")
print("=" * 80)

# Préparation
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User, PasswordResetToken

test_email = "scenario@example.com"
original_password = "MyOriginal@Pass123"

# Nettoyer
try:
    User.objects.get(email=test_email).delete()
except User.DoesNotExist:
    pass

# Étape 1: Création du compte
print("\n📝 ÉTAPE 1: L'utilisateur crée son compte")
print(f"   Email: {test_email}")
print(f"   Mot de passe: {original_password}")

response = requests.post(
    f"{BASE_URL}/api/auth/register/",
    json={
        "email": test_email,
        "password": original_password,
        "full_name": "Scénario Test User",
        "country": "Benin"
    }
)
assert response.status_code == 201
user_id = response.json()['user_id']
print(f"   ✓ Compte créé avec succès (ID: {user_id})")

# Étape 2: Connexion réussie
print("\n🔐 ÉTAPE 2: L'utilisateur se connecte avec succès")
response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": original_password
    }
)
assert response.status_code == 200
print(f"   ✓ Connexion réussie")

# Étape 3: L'utilisateur oublie son mot de passe
print("\n😰 ÉTAPE 3: L'utilisateur oublie son mot de passe")
print("   Il essaie de se connecter avec un mauvais mot de passe...")

response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": "WrongPassword@123"
    }
)
assert response.status_code == 401
print(f"   ✗ Connexion échouée (comme attendu)")

# Étape 4: Demande de réinitialisation
print("\n📧 ÉTAPE 4: L'utilisateur demande la réinitialisation")
print(f"   Il va sur /password-reset/ et entre son email: {test_email}")

response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={"email": test_email}
)
assert response.status_code == 200
print(f"   ✓ Demande envoyée avec succès")
print(f"   ✓ Message: {response.json()['message']}")

# Simuler la réception de l'email
time.sleep(0.5)
user = User.objects.get(email=test_email)
reset_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at')
reset_link = f"{BASE_URL}/password-reset/confirm/?token={reset_token.token}"
print(f"\n   📬 Email reçu avec le lien:")
print(f"   🔗 {reset_link}")

# Étape 5: Clic sur le lien et création d'un nouveau mot de passe
print("\n🔑 ÉTAPE 5: L'utilisateur clique sur le lien et crée un nouveau mot de passe")
new_password = "MyNewSecure@Pass456"
print(f"   Nouveau mot de passe: {new_password}")

response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": reset_token.token,
        "new_password": new_password
    }
)
assert response.status_code == 200
print(f"   ✓ Mot de passe réinitialisé avec succès")

# Étape 6: Vérification que l'ancien mot de passe ne fonctionne plus
print("\n🔒 ÉTAPE 6: Vérification de la sécurité")
print("   Test avec l'ancien mot de passe...")

response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": original_password
    }
)
assert response.status_code == 401
print(f"   ✓ Ancien mot de passe rejeté (sécurité OK)")

# Étape 7: Connexion avec le nouveau mot de passe
print("\n✅ ÉTAPE 7: Connexion avec le nouveau mot de passe")

response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": test_email,
        "password": new_password
    }
)
assert response.status_code == 200
print(f"   ✓ Connexion réussie avec le nouveau mot de passe!")
print(f"   ✓ L'utilisateur a retrouvé l'accès à son compte")

# Cas d'erreur: Tentative de réutilisation du lien
print("\n🛡️  ÉTAPE 8: Test de sécurité - Réutilisation du lien")
print("   Quelqu'un essaie de réutiliser l'ancien lien...")

response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": reset_token.token,
        "new_password": "Hacker@Password123"
    }
)
assert response.status_code == 400
print(f"   ✓ Lien rejeté (déjà utilisé)")
print(f"   ✓ Le compte reste sécurisé")

print("\n" + "=" * 80)
print("✅ SCÉNARIO COMPLET RÉUSSI!")
print("=" * 80)
print("\n📊 RÉSUMÉ:")
print("   ✓ Création de compte")
print("   ✓ Connexion initiale")
print("   ✓ Demande de réinitialisation")
print("   ✓ Réception du lien par email")
print("   ✓ Réinitialisation du mot de passe")
print("   ✓ Ancien mot de passe invalidé")
print("   ✓ Connexion avec nouveau mot de passe")
print("   ✓ Protection contre réutilisation du lien")
print("\n🎉 L'utilisateur peut TOUJOURS récupérer son accès!")

# Nettoyage
user.delete()
print("\n🧹 Nettoyage effectué")
