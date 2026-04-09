# Utilisation d'une image Python officielle
FROM python:3.13-slim

# Configuration de l'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système (Tesseract OCR + Poppler pour PDF)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    libpq-dev \
    gcc \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Variables pour Django
ENV STATIC_ROOT=/app/staticfiles

# Copie du code source
COPY . /app/

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Port d'écoute (Render utilise souvent 10000)
EXPOSE 10000

# Script de démarrage : Migrations + Gunicorn
# On utilise la forme 'shell' pour permettre l'enchaînement des commandes
CMD python manage.py migrate && gunicorn --bind 0.0.0.0:10000 config.wsgi:application
