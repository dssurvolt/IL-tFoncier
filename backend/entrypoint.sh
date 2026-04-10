#!/bin/bash

# Attendre que la DB soit prête si nécessaire
echo "⏳ Attente de la base de données Supabase..."
sleep 2

# Forcer les migrations
echo "🚀 Lancement des migrations Django..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Lancer le serveur
echo "✅ Démarrage de Gunicorn..."
exec gunicorn --bind 0.0.0.0:10000 config.wsgi:application
