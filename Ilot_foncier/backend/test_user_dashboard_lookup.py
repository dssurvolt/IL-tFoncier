import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

# Créer un utilisateur
try:
    user = User.objects.create_user(
        email="lookup_test@example.com",
        password="TestPassword@123",
        full_name="Lookup Test User"
    )
    print(f"Created user: {user.email} (ID: {user.id})")
    print(f"User ID type: {type(user.id)}")
    
    # Simuler le dashboard
    identifier_str = str(user.id)
    print(f"Identifier string: {identifier_str}")
    
    try:
        val = uuid.UUID(identifier_str)
        print(f"UUID object: {val}")
        
        found_user = User.objects.get(id=val)
        print(f"Found user via UUID object: {found_user}")
        
    except Exception as e:
        print(f"Error finding via UUID object: {e}")

    try:
        found_user_str = User.objects.get(id=identifier_str)
        print(f"Found user via string: {found_user_str}")
    except Exception as e:
        print(f"Error finding via string: {e}")
        
    # Nettoyage
    user.delete()
    
except Exception as e:
    print(f"Setup failed: {e}")
