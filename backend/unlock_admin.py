import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

try:
    user = User.objects.get(email='rakib.sobabe@epitech.eu')
    user.set_password('AdminSelection2026!')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("✅ Portes de l'administration déverrouillées avec succès !")
except Exception as e:
    print(f"❌ Erreur : {e}")
