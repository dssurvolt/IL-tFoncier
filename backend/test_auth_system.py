#!/usr/bin/env python
"""Script de test complet pour le système d'authentification"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_register_success():
    """Test 1: Inscription réussie avec un mot de passe fort"""
    print("\n🧪 Test 1: Inscription réussie")
    data = {
        "email": "test@example.com",
        "password": "Test@2024Strong!",
        "full_name": "Jean Dupont",
        "country": "Benin",
        "district": "Cotonou"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 201, "L'inscription devrait réussir"
    print("   ✓ PASS")
    return response.json()['user_id']

def test_register_duplicate_email():
    """Test 2: Inscription avec email déjà existant"""
    print("\n🧪 Test 2: Email déjà existant")
    data = {
        "email": "test@example.com",
        "password": "Test@2024Strong!",
        "full_name": "Marie Martin",
        "country": "Benin"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Devrait échouer (email déjà utilisé)"
    assert "existe déjà" in response.json()['error'].lower()
    print("   ✓ PASS")

def test_register_weak_password():
    """Test 3: Inscription avec mot de passe faible"""
    print("\n🧪 Test 3: Mot de passe trop faible")
    data = {
        "email": "weak@example.com",
        "password": "123",
        "full_name": "Paul Faible",
        "country": "Benin"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Devrait échouer (mot de passe trop court)"
    assert "8 caractères" in response.json()['error']
    print("   ✓ PASS")

def test_register_missing_fields():
    """Test 4: Inscription avec champs manquants"""
    print("\n🧪 Test 4: Champs manquants")
    data = {
        "email": "incomplete@example.com",
        "password": "Test@2024!"
        # Manque full_name
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Devrait échouer (champs manquants)"
    print("   ✓ PASS")

def test_login_success():
    """Test 5: Connexion réussie"""
    print("\n🧪 Test 5: Connexion réussie")
    data = {
        "email": "test@example.com",
        "password": "Test@2024Strong!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "La connexion devrait réussir"
    assert 'user_id' in response.json()
    print("   ✓ PASS")

def test_login_wrong_password():
    """Test 6: Connexion avec mauvais mot de passe"""
    print("\n🧪 Test 6: Mauvais mot de passe")
    data = {
        "email": "test@example.com",
        "password": "WrongPassword123!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Devrait échouer (mauvais mot de passe)"
    assert "incorrect" in response.json()['error'].lower()
    print("   ✓ PASS")

def test_login_nonexistent_user():
    """Test 7: Connexion avec utilisateur inexistant"""
    print("\n🧪 Test 7: Utilisateur inexistant")
    data = {
        "email": "nonexistent@example.com",
        "password": "Test@2024!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Devrait échouer (utilisateur inexistant)"
    print("   ✓ PASS")

def test_login_missing_credentials():
    """Test 8: Connexion sans identifiants"""
    print("\n🧪 Test 8: Identifiants manquants")
    data = {
        "email": "test@example.com"
        # Manque password
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Devrait échouer (identifiants manquants)"
    print("   ✓ PASS")

def test_admin_login():
    """Test 9: Connexion admin"""
    print("\n🧪 Test 9: Connexion administrateur")
    data = {
        "email": "admin@ilotfoncier.bj",
        "password": "Admin@2024"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "La connexion admin devrait réussir"
    assert response.json()['role'] == 'ADMIN'
    print("   ✓ PASS")

def test_case_insensitive_email():
    """Test 10: Email insensible à la casse"""
    print("\n🧪 Test 10: Email en majuscules")
    data = {
        "email": "TEST@EXAMPLE.COM",
        "password": "Test@2024Strong!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Devrait réussir (email insensible à la casse)"
    print("   ✓ PASS")

def cleanup():
    """Nettoyage: Supprimer l'utilisateur de test"""
    print("\n🧹 Nettoyage...")
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    from identity.models import User
    
    try:
        user = User.objects.get(email='test@example.com')
        user.delete()
        print("   ✓ Utilisateur de test supprimé")
    except User.DoesNotExist:
        print("   ℹ Aucun utilisateur de test à supprimer")

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 TESTS DU SYSTÈME D'AUTHENTIFICATION")
    print("=" * 60)
    
    try:
        # Tests d'inscription
        user_id = test_register_success()
        test_register_duplicate_email()
        test_register_weak_password()
        test_register_missing_fields()
        
        # Tests de connexion
        test_login_success()
        test_login_wrong_password()
        test_login_nonexistent_user()
        test_login_missing_credentials()
        test_admin_login()
        test_case_insensitive_email()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Le serveur Django n'est pas accessible")
        print("   Assurez-vous que le serveur tourne sur http://127.0.0.1:8000")
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
    finally:
        cleanup()
