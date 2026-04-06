import os
import django
from django.conf import settings
from django.template import Template, Context

# Config standard pour test local
if not settings.configured:
    settings.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}])
    django.setup()

tpl_content = """
<div class="fw-bold small text-dark lh-1" style="font-size: 0.75rem;">{{ user.full_name|default:user.email|truncatechars:15 }}</div>
"""

user = type('User', (), {'full_name': 'Jean Dupont', 'email': 'jean@example.com'})()
t = Template(tpl_content)
print(t.render(Context({'user': user})))
