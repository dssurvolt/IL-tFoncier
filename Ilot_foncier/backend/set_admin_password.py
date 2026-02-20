#!/usr/bin/env python
"""Script pour définir le mot de passe du superutilisateur"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

# Définir le mot de passe pour l'admin
admin = User.objects.get(email='admin@ilotfoncier.bj')
admin.set_password('Admin@2024')
admin.save()

print(f"✓ Mot de passe défini pour {admin.email}")
print(f"  Email: admin@ilotfoncier.bj")
print(f"  Password: Admin@2024")
