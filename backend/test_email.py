import os
import django
from django.core.mail import send_mail

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_email():
    print("📧 Tentative d'envoi d'un mail de test...")
    try:
        send_mail(
            'Test iLôt Foncier',
            'Ceci est un test d\'envoi d\'email depuis le projet iLôt Foncier.',
            'sobaberakib4@gmail.com',
            ['rakib.sobabe@epitech.eu'],
            fail_silently=False,
        )
        print("✅ Email envoyé avec succès !")
    except Exception as e:
        print(f"❌ Échec de l'envoi : {e}")

if __name__ == "__main__":
    test_email()
