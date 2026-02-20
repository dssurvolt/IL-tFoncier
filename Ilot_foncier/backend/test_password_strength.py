#!/usr/bin/env python
"""Test de validation de la force du mot de passe"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

test_passwords = [
    ("123", False, "Trop court (3 caractères)"),
    ("12345678", False, "8 caractères mais pas de majuscule/minuscule/spécial"),
    ("Password", False, "Pas de chiffre ni caractère spécial"),
    ("Password123", False, "Pas de caractère spécial"),
    ("Password@123", True, "Mot de passe fort (tous les critères)"),
    ("MyP@ss1", False, "Seulement 7 caractères"),
    ("ALLUPPERCASE123!", False, "Pas de minuscule"),
    ("alllowercase123!", False, "Pas de majuscule"),
    ("NoNumbers!@#", False, "Pas de chiffre"),
    ("Test@2024", True, "Mot de passe fort"),
    ("Azerty@1", True, "Mot de passe fort minimal"),
]

print("=" * 70)
print("🔒 TEST DE VALIDATION DE LA FORCE DU MOT DE PASSE")
print("=" * 70)

passed = 0
failed = 0

for password, should_pass, description in test_passwords:
    print(f"\n📝 Test: {description}")
    print(f"   Mot de passe: '{password}'")
    
    data = {
        "email": f"test_{len(password)}@example.com",
        "password": password,
        "full_name": "Test User",
        "country": "Benin"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=data)
    
    if should_pass:
        if response.status_code == 201:
            print(f"   ✓ PASS - Inscription réussie comme attendu")
            passed += 1
            # Nettoyer
            import os
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            from identity.models import User
            try:
                user = User.objects.get(email=data['email'])
                user.delete()
            except:
                pass
        else:
            print(f"   ✗ FAIL - Devrait réussir mais a échoué: {response.json()}")
            failed += 1
    else:
        if response.status_code != 201:
            print(f"   ✓ PASS - Rejeté comme attendu: {response.json().get('error', 'Erreur')}")
            passed += 1
        else:
            print(f"   ✗ FAIL - Devrait être rejeté mais a réussi")
            failed += 1
            # Nettoyer
            import os
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            from identity.models import User
            try:
                user = User.objects.get(email=data['email'])
                user.delete()
            except:
                pass

print("\n" + "=" * 70)
print(f"📊 RÉSULTATS: {passed} réussis, {failed} échoués sur {len(test_passwords)} tests")
if failed == 0:
    print("✅ TOUS LES TESTS SONT PASSÉS!")
else:
    print(f"❌ {failed} test(s) ont échoué")
print("=" * 70)
