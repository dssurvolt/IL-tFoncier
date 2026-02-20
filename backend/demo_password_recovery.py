#!/usr/bin/env python
"""Démonstration du système de récupération avec l'utilisateur démo"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🎬 DÉMONSTRATION: RÉCUPÉRATION D'ACCÈS POUR L'UTILISATEUR DÉMO")
print("=" * 80)

demo_email = "demo@ilotfoncier.bj"
old_password = "Demo@2024!"
new_password = "DemoRecovered@2024!"

print(f"\n📧 Email de l'utilisateur démo: {demo_email}")
print(f"🔑 Mot de passe actuel: {old_password}")

# Étape 1: Vérifier que le compte existe et fonctionne
print("\n✅ ÉTAPE 1: Vérification du compte existant")
response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": demo_email,
        "password": old_password
    }
)

if response.status_code == 200:
    print(f"   ✓ Le compte existe et fonctionne")
    user_id = response.json()['user_id']
    print(f"   ✓ User ID: {user_id}")
else:
    print(f"   ✗ Le compte n'existe pas ou le mot de passe est incorrect")
    print(f"   Créons le compte...")
    
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    from identity.models import User
    
    user = User.objects.create_user(
        email=demo_email,
        password=old_password,
        full_name="Utilisateur Démo",
        country="Benin",
        district="Cotonou"
    )
    user_id = str(user.id)
    print(f"   ✓ Compte créé (ID: {user_id})")

# Étape 2: Demander la réinitialisation
print("\n📧 ÉTAPE 2: Demande de réinitialisation du mot de passe")
print(f"   L'utilisateur va sur: {BASE_URL}/password-reset/")
print(f"   Il entre son email: {demo_email}")

response = requests.post(
    f"{BASE_URL}/api/password-reset/request/",
    json={"email": demo_email}
)

if response.status_code == 200:
    print(f"   ✓ Demande envoyée avec succès")
    print(f"   ✓ {response.json()['message']}")
else:
    print(f"   ✗ Erreur: {response.json()}")
    exit(1)

# Récupérer le token
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User, PasswordResetToken

time.sleep(0.5)
user = User.objects.get(email=demo_email)
reset_token = PasswordResetToken.objects.filter(user=user, used=False).latest('created_at')

print(f"\n   📬 Email simulé reçu:")
print(f"   " + "─" * 76)
print(f"   │ De: iLôt Foncier <noreply@ilotfoncier.bj>")
print(f"   │ À: {demo_email}")
print(f"   │ Sujet: Réinitialisation de votre mot de passe")
print(f"   │")
print(f"   │ Bonjour Utilisateur Démo,")
print(f"   │")
print(f"   │ Vous avez demandé la réinitialisation de votre mot de passe.")
print(f"   │")
print(f"   │ Cliquez sur le lien ci-dessous:")
print(f"   │ {BASE_URL}/password-reset/confirm/?token={reset_token.token}")
print(f"   │")
print(f"   │ Ce lien est valide pendant 1 heure.")
print(f"   │")
print(f"   │ Cordialement,")
print(f"   │ L'équipe iLôt Foncier")
print(f"   " + "─" * 76)

# Étape 3: Réinitialiser le mot de passe
print(f"\n🔑 ÉTAPE 3: Réinitialisation du mot de passe")
print(f"   L'utilisateur clique sur le lien et entre un nouveau mot de passe")
print(f"   Nouveau mot de passe: {new_password}")

response = requests.post(
    f"{BASE_URL}/api/password-reset/confirm/",
    json={
        "token": reset_token.token,
        "new_password": new_password
    }
)

if response.status_code == 200:
    print(f"   ✓ Mot de passe réinitialisé avec succès!")
else:
    print(f"   ✗ Erreur: {response.json()}")
    exit(1)

# Étape 4: Vérifier que l'ancien mot de passe ne fonctionne plus
print(f"\n🔒 ÉTAPE 4: Test de sécurité")
print(f"   Tentative de connexion avec l'ancien mot de passe...")

response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": demo_email,
        "password": old_password
    }
)

if response.status_code == 401:
    print(f"   ✓ Ancien mot de passe rejeté (sécurité OK)")
else:
    print(f"   ✗ PROBLÈME: L'ancien mot de passe fonctionne encore!")
    exit(1)

# Étape 5: Connexion avec le nouveau mot de passe
print(f"\n✅ ÉTAPE 5: Connexion avec le nouveau mot de passe")

response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={
        "email": demo_email,
        "password": new_password
    }
)

if response.status_code == 200:
    print(f"   ✓ Connexion réussie!")
    print(f"   ✓ L'utilisateur a retrouvé l'accès à son compte")
    data = response.json()
    print(f"\n   📊 Informations du compte:")
    print(f"      • Email: {data['email']}")
    print(f"      • Nom: {data['full_name']}")
    print(f"      • Rôle: {data['role']}")
    print(f"      • ID: {data['user_id']}")
else:
    print(f"   ✗ Erreur de connexion: {response.json()}")
    exit(1)

print("\n" + "=" * 80)
print("✅ DÉMONSTRATION RÉUSSIE!")
print("=" * 80)
print("\n🎯 NOUVEAUX IDENTIFIANTS DE L'UTILISATEUR DÉMO:")
print(f"   📧 Email: {demo_email}")
print(f"   🔑 Mot de passe: {new_password}")
print(f"\n🔗 Vous pouvez vous connecter sur: {BASE_URL}/login/")
print("=" * 80)
