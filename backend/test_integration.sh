#!/bin/bash
# Script de test d'intégration complète

echo "======================================"
echo "🧪 TEST D'INTÉGRATION COMPLÈTE"
echo "======================================"

# Test 1: Inscription d'un nouvel utilisateur
echo -e "\n📝 Test 1: Inscription d'un nouvel utilisateur"
REGISTER_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration@test.com",
    "password": "IntegrationTest@2024!",
    "full_name": "Test Integration",
    "country": "Benin",
    "district": "Cotonou"
  }')

echo "Response: $REGISTER_RESPONSE"

# Extraire l'ID utilisateur
USER_ID=$(echo $REGISTER_RESPONSE | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
echo "User ID créé: $USER_ID"

# Test 2: Connexion avec les identifiants
echo -e "\n🔐 Test 2: Connexion avec les identifiants"
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration@test.com",
    "password": "IntegrationTest@2024!"
  }')

echo "Response: $LOGIN_RESPONSE"

# Test 3: Tentative de connexion avec mauvais mot de passe
echo -e "\n❌ Test 3: Connexion avec mauvais mot de passe"
WRONG_LOGIN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration@test.com",
    "password": "WrongPassword123!"
  }')

echo "Response: $WRONG_LOGIN"

# Test 4: Tentative d'inscription avec email existant
echo -e "\n⚠️  Test 4: Inscription avec email déjà utilisé"
DUPLICATE_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration@test.com",
    "password": "AnotherPassword@2024!",
    "full_name": "Another User",
    "country": "Benin"
  }')

echo "Response: $DUPLICATE_RESPONSE"

# Test 5: Vérifier que la page de login affiche bien le formulaire email
echo -e "\n🌐 Test 5: Vérification de la page de login"
LOGIN_PAGE=$(curl -s http://127.0.0.1:8000/login/)
if echo "$LOGIN_PAGE" | grep -q "ADRESSE EMAIL"; then
    echo "✓ La page de login affiche bien le champ email"
else
    echo "✗ Erreur: La page de login ne contient pas le champ email"
fi

# Test 6: Vérifier que la page de register affiche la validation du mot de passe
echo -e "\n🌐 Test 6: Vérification de la page d'inscription"
REGISTER_PAGE=$(curl -s http://127.0.0.1:8000/register/)
if echo "$REGISTER_PAGE" | grep -q "checkPasswordStrength"; then
    echo "✓ La page d'inscription contient la validation en temps réel"
else
    echo "✗ Erreur: La validation du mot de passe n'est pas présente"
fi

if echo "$REGISTER_PAGE" | grep -q "Au moins 8 caractères"; then
    echo "✓ Les critères de mot de passe sont affichés"
else
    echo "✗ Erreur: Les critères de mot de passe ne sont pas affichés"
fi

echo -e "\n======================================"
echo "✅ TESTS D'INTÉGRATION TERMINÉS"
echo "======================================"

# Nettoyage
echo -e "\n🧹 Nettoyage de l'utilisateur de test..."
python3 << EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from identity.models import User
try:
    user = User.objects.get(email='integration@test.com')
    user.delete()
    print("✓ Utilisateur de test supprimé")
except User.DoesNotExist:
    print("ℹ Aucun utilisateur à supprimer")
EOF
