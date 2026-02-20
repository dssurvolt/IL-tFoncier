#!/usr/bin/env python
"""Créer un utilisateur de démonstration pour tester l'interface"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

# Créer un utilisateur de démo
email = "demo@ilotfoncier.bj"
password = "Demo@2024!"

# Supprimer s'il existe déjà
try:
    existing = User.objects.get(email=email)
    existing.delete()
    print(f"✓ Ancien utilisateur {email} supprimé")
except User.DoesNotExist:
    pass

# Créer le nouvel utilisateur
user = User.objects.create_user(
    email=email,
    password=password,
    full_name="Utilisateur Démo",
    country="Benin",
    district="Cotonou",
    role=User.Role.USER
)

print("\n" + "=" * 60)
print("✅ UTILISATEUR DE DÉMONSTRATION CRÉÉ")
print("=" * 60)
print(f"\n📧 Email    : {email}")
print(f"🔑 Password : {password}")
print(f"👤 Nom      : {user.full_name}")
print(f"🆔 User ID  : {user.id}")
print(f"📍 Pays     : {user.country}")
print(f"🏛️  District : {user.district}")
print(f"⭐ Rôle     : {user.role}")
print("\n" + "=" * 60)
print("🌐 ACCÈS")
print("=" * 60)
print(f"\n🔗 Page de connexion : http://127.0.0.1:8000/login/")
print(f"🔗 Dashboard         : http://127.0.0.1:8000/dashboard/{user.id}/")
print("\n" + "=" * 60)
