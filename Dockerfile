# Utilisation d'une image Python officielle légère
FROM python:3.12-slim-bookworm

# Éviter que Python ne génère des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Désactiver le buffering pour voir les logs en temps réel
ENV PYTHONUNBUFFERED 1

# Installation des dépendances système (Tesseract OCR pour l'extraction de titres fonciers)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libpq-dev \
    gcc \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Installation des dépendances Python
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source du dossier backend
COPY backend/ /app/

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposition du port (Render utilise souvent le port 10000 par défaut ou via PORT env)
EXPOSE 10000

# Commande de démarrage avec Gunicorn
# On utilise --bind 0.0.0.0:$PORT pour que Render puisse router le trafic
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000}
