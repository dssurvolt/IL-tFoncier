import os
import django
import json
from django.test import Client
from django.urls import reverse
from identity.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_login():
    c = Client()
    # Create test user
    email = "test_leak@example.com"
    password = "Password123!"
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(email=email, password=password, full_name=None)
        print(f"User created with full_name=None. ID: {user.id}")
    else:
        user = User.objects.get(email=email)
        user.full_name = None
        user.save()
        print(f"User updated with full_name=None. ID: {user.id}")

    # Test API Login
    login_url = reverse('api_auth', kwargs={'action': 'login'})
    response = c.post(login_url, data=json.dumps({'email': email, 'password': password}), content_type='application/json')
    data = response.json()
    print(f"API Login Response: {data}")

    # Visit dashboard
    dashboard_url = reverse('user_dashboard', kwargs={'wallet': str(user.id)})
    response = c.get(dashboard_url)
    print(f"Dashboard status: {response.status_code}")
    content = response.content.decode('utf-8')
    
    # Check for "None" in the rendered HTML
    if "Bonjour, None" in content:
        print("❌ CRITICAL: 'Bonjour, None' found in dashboard content.")
    else:
        print("✅ 'Bonjour, None' not found in dashboard content.")
    
    if "Connecté en tant que" in content:
        # Check navUserName
        import re
        match = re.search(r'id="navUserName".*?>(.*?)</span>', content, re.DOTALL)
        if match:
            name = match.group(1).strip()
            print(f"navUserName content: '{name}'")
            if name == "None":
                print("❌ CRITICAL: 'navUserName' is 'None'.")
            else:
                print(f"✅ 'navUserName' is '{name}'.")

test_login()
