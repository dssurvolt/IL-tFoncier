import os
import django
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User

def investigate_context():
    print("🔍 INVESTIGATION DU CONTEXTE POUR RAKIB...")
    client = Client()
    
    # Login Rakib
    email = "rakib.sobabe@ilot.bj"
    password = "Rakib2026Password"
    client.login(username=email, password=password)
    
    # Voir 'Mes Transactions'
    url = reverse('user_transactions')
    response = client.get(url)
    
    print(f"📡 Status: {response.status_code}")
    
    # On va vérifier les variables de contexte fournies par les context processors
    # Note: Dans un Client test, on peut voir le contexte via response.context_data
    # ou essayer de trouver la variable is_notary
    
    if hasattr(response, 'context'):
        is_notary = response.context.get('is_notary')
        print(f"🛡️ Variable 'is_notary' dans le template : {is_notary}")
        
    # Vérifier le role de l'utilisateur vu par le template
    user_in_template = response.context.get('user')
    if user_in_template:
        print(f"👤 Role utilisateur vu par le template : {user_in_template.role}")
        print(f"⚖️ Est-ce égal à User.Role.NOTARY ('NOTARY') ? : {user_in_template.role == User.Role.NOTARY}")

    # Inspecter le contenu HTML pour les classes spécifiques aux notaires
    content = response.content.decode()
    if 'Espace Notaire' in content:
        print("🚨 ALERTE : La chaîne 'Espace Notaire' a été trouvée dans le HTML final !")
    
    if 'Mes Transactions Sécurisées' in content:
        print("✅ La chaîne 'Mes Transactions Sécurisées' est présente.")

if __name__ == "__main__":
    investigate_context()
