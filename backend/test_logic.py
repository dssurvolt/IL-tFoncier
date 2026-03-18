import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from notaries.context_processors import notary_context

def test_roles_and_logic():
    print("🚦 Test des rôles et de la logique de redirection...")
    
    # 1. RAKIB (USER)
    rakib = User.objects.filter(full_name='Rakib SOBABE').first()
    if rakib:
        print(f"👤 Rakib: Email={rakib.email}, Role={rakib.role}")
        
        # Test Notary Context Processor
        factory = RequestFactory()
        request = factory.get('/')
        request.user = rakib
        context = notary_context(request)
        print(f"🛡️ Is Notary (Rakib): {context['is_notary']}")
        assert context['is_notary'] is False

    # 2. AKOFFODJI (NOTARY)
    ak = User.objects.filter(email='jp.akoffodji@notariat.bj').first()
    if ak:
        print(f"⚖️ Akoffodji: Email={ak.email}, Role={ak.role}")
        request = factory.get('/')
        request.user = ak
        context = notary_context(request)
        print(f"🛡️ Is Notary (Akoffodji): {context['is_notary']}")
        assert context['is_notary'] is True

    print("\n✅ Logique de base validée.")

if __name__ == "__main__":
    test_roles_and_logic()
