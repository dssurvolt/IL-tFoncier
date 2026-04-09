#!/usr/bin/env bash
# Script de build personnalisé pour Render.com
# Ce script installe les dépendances système nécessaires (Tesseract OCR, Poppler)
# et prépare l'application Django.

set -o errexit

echo "--- 🛠️  Installation des dépendances système ---"

# Note: Sur Render (Standard Python Runtime), apt-get n'est pas toujours accessible directement.
# Si vous utilisez un environnement Docker, utilisez le Dockerfile fourni.
# Pour le runtime Python standard, ce script tente d'installer via apt-get.

if command -v apt-get >/dev/null; then
    # Mise à jour et installation des outils OCR et PDF
    # On utilise || true pour ne pas faire échouer le build si apt-get est bridé (Runtime standard)
    apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils || echo "⚠️ Impossible d'exécuter apt-get. Si l'OCR échoue, passez à un environnement Docker."
else
    echo "⚠️ apt-get non trouvé. Ignoré."
fi

echo "--- 📦 Installation des dépendances Python ---"
pip install -r requirements.txt

echo "--- 🏗️  Migrations & Collectstatic ---"
python manage.py migrate
python manage.py collectstatic --no-input

echo "--- ✅ Build terminé avec succès ---"
