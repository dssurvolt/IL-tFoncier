import os
import django
from django.conf import settings
from django.template import Template, Context

# Config standard pour test local
if not settings.configured:
    settings.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}])
    django.setup()

# Test Case 1: Nav Bar Brand/User
user = type('User', (), {
    'full_name': 'ABD RAKIB SOBABE A. T.',
    'email': 'rakib@example.com',
    'get_role_display': 'Utilisateur Standard'
})()

nav_tpl = '<div class="fw-bold small text-dark lh-1">{{ user.full_name|default:user.email|truncatechars:18 }}</div>'
t1 = Template(nav_tpl)
print("Nav Name Render:", t1.render(Context({'user': user})))

avatar_tpl = '{{ user.full_name|slice:":1"|default:"U" }}'
t2 = Template(avatar_tpl)
print("Avatar Render:", t2.render(Context({'user': user})))

# Test Case 2: Marketplace Card
listing = type('Listing', (), {
    'property': type('Property', (), {
        'owner_wallet': type('User', (), {
            'full_name': 'ABD RAKIB SOBABE A. T.',
            'wallet_address': '0x1234567890abcdef...',
            'is_verified': True
        })(),
        'district': 'Akpakpa',
        'country': 'Benin'
    })()
})()

card_tpl = '{{ listing.property.district }}, {{ listing.property.country }}'
t3 = Template(card_tpl)
print("Card Location Render:", t3.render(Context({'listing': listing})))

owner_tpl = '{{ listing.property.owner_wallet.full_name|default:listing.property.owner_wallet.wallet_address|truncatechars:12 }}'
t4 = Template(owner_tpl)
print("Card Owner Render:", t4.render(Context({'listing': listing})))
