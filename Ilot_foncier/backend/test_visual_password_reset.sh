#!/bin/bash
# Test visuel complet du système de récupération

echo "======================================================================"
echo "🎨 TEST VISUEL DU SYSTÈME DE RÉCUPÉRATION DE MOT DE PASSE"
echo "======================================================================"

# Test 1: Page de demande de réinitialisation
echo -e "\n📄 Test 1: Page /password-reset/"
echo "   Vérification du contenu..."

PAGE=$(curl -s http://127.0.0.1:8000/password-reset/)

if echo "$PAGE" | grep -q "Mot de passe oublié"; then
    echo "   ✓ Titre correct"
else
    echo "   ✗ Titre manquant"
fi

if echo "$PAGE" | grep -q "ADRESSE EMAIL"; then
    echo "   ✓ Champ email présent"
else
    echo "   ✗ Champ email manquant"
fi

if echo "$PAGE" | grep -q "ENVOYER LE LIEN"; then
    echo "   ✓ Bouton d'envoi présent"
else
    echo "   ✗ Bouton manquant"
fi

if echo "$PAGE" | grep -q "Retour à la connexion"; then
    echo "   ✓ Lien retour présent"
else
    echo "   ✗ Lien retour manquant"
fi

# Test 2: Page de confirmation
echo -e "\n📄 Test 2: Page /password-reset/confirm/"
echo "   Vérification du contenu..."

PAGE=$(curl -s "http://127.0.0.1:8000/password-reset/confirm/?token=test")

if echo "$PAGE" | grep -q "Nouveau mot de passe"; then
    echo "   ✓ Titre correct"
else
    echo "   ✗ Titre manquant"
fi

if echo "$PAGE" | grep -q "Au moins 8 caractères"; then
    echo "   ✓ Critères de mot de passe affichés"
else
    echo "   ✗ Critères manquants"
fi

if echo "$PAGE" | grep -q "checkPasswordStrength"; then
    echo "   ✓ Validation en temps réel présente"
else
    echo "   ✗ Validation manquante"
fi

if echo "$PAGE" | grep -q "RÉINITIALISER"; then
    echo "   ✓ Bouton de réinitialisation présent"
else
    echo "   ✗ Bouton manquant"
fi

# Test 3: API de demande
echo -e "\n🔌 Test 3: API /api/password-reset/request/"

RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/password-reset/request/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}')

if echo "$RESPONSE" | grep -q "success"; then
    echo "   ✓ API fonctionne"
    echo "   Response: $RESPONSE"
else
    echo "   ✗ API ne répond pas correctement"
fi

# Test 4: Lien depuis la page de login
echo -e "\n🔗 Test 4: Lien depuis /login/"

LOGIN_PAGE=$(curl -s http://127.0.0.1:8000/login/)

if echo "$LOGIN_PAGE" | grep -q "Mot de passe oublié"; then
    echo "   ✓ Lien 'Mot de passe oublié' présent sur la page de login"
else
    echo "   ✗ Lien manquant sur la page de login"
fi

if echo "$LOGIN_PAGE" | grep -q "web_password_reset"; then
    echo "   ✓ Lien pointe vers la bonne URL"
else
    echo "   ✗ URL incorrecte"
fi

echo -e "\n======================================================================"
echo "✅ TESTS VISUELS TERMINÉS"
echo "======================================================================"
echo -e "\n📋 Pages disponibles:"
echo "   • http://127.0.0.1:8000/login/"
echo "   • http://127.0.0.1:8000/password-reset/"
echo "   • http://127.0.0.1:8000/password-reset/confirm/?token=..."
echo -e "\n🔌 API disponibles:"
echo "   • POST /api/password-reset/request/"
echo "   • POST /api/password-reset/confirm/"
