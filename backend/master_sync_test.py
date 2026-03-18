import os
import django
import uuid
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from identity.models import User
from land_registry.models import Property
from notaries.models import Notary, TransactionFolio
from marketplace.models import Listing

def test_three_party_synchronization():
    print("🚀 --- TEST DE SYNCHRONISATION ENTRE LES 3 PARTIES ---")
    client_rakib = Client()
    client_ousmane = Client()
    client_notaire = Client()

    # 1. SETUP DES ACTEURS
    rakib_email = "temp_be4ff30a-8863-4d8c-8d00-a80da480d615@ilot.bj"
    ousmane_email = "ousmane.alfa@exemple.com"
    notaire_email = "jp.akoffodji@notariat.bj"
    password = "Notaire2026Password" # Notaire has this password
    password_ous = "Ousmane2026"
    password_rak = "Notaire2026Password" # From setup_rakib_scenario maybe? Let's assume standard for tests.
    
    # Check/Create Rakib (Ensure he has a password we know)
    rakib = User.objects.get(email=rakib_email)
    rakib.set_password("Rakib2026")
    rakib.save()
    
    # Check/Create Ousmane
    ousmane, _ = User.objects.get_or_create(
        email=ousmane_email,
        defaults={
            'full_name': "Ousmane ALFA",
            'role': User.Role.USER,
            'wallet_address': f"0x{uuid.uuid4().hex[:40]}"
        }
    )
    ousmane.set_password("Ousmane2026")
    ousmane.save()
    
    # Me Akoffodji
    notaire_u = User.objects.get(email=notaire_email)
    notaire_u.set_password("Notaire2026") # Use a clean password for test
    notaire_u.save()
    notaire_profile = Notary.objects.get(user=notaire_u)

    # Property
    prop, _ = Property.objects.get_or_create(
        village="Lot 405 - Cadjèhoun",
        owner_wallet=ousmane,
        defaults={
            'status': Property.Status.ON_CHAIN,
            'gps_centroid': {"lat": 6.353, "lng": 2.392},
            'gps_boundaries': [{"lat": 6.353, "lng": 2.392}, {"lat": 6.354, "lng": 2.392}]
        }
    )

    # CLEANUP FOLLIOS: Supprimer TOUS les folios concernant cette propriété
    TransactionFolio.objects.filter(property=prop).delete()
    print("🧹 Base de données nettoyée de tous les anciens folios pour cette parcelle.")

    # 2. INITIALISATION (Étape 1)
    folio = TransactionFolio.objects.create(
        property=prop,
        buyer=rakib,
        seller=ousmane,
        notary=notaire_profile,
        status=TransactionFolio.Step.STEP1_NOTARY_SELECTED
    )
    print(f"🎬 Folio {folio.id} créé à l'étape 1.")

    # 3. VÉRIFICATION ÉTAPE 1 (ACHETEUR / VENDEUR)
    # Login Rakib
    logged_rak = client_rakib.login(username=rakib_email, password="Rakib2026")
    print(f"🔑 Login Rakib: {'SUCCÈS' if logged_rak else 'ÉCHEC'}")
    
    url_rak = reverse('web_transaction_status', kwargs={'folio_id': folio.id})
    resp_rak = client_rakib.get(url_rak, follow=True)
    print(f"📡 Response Rakib: {resp_rak.status_code}")
    print(f"📍 URL Finale: {resp_rak.request['PATH_INFO']}")
    if resp_rak.redirect_chain:
        print(f"↩️ Redirect Chain: {resp_rak.redirect_chain}")

    if resp_rak.context is None:
        print("❌ Erreur: context est None.")
        print(f"📄 Début du contenu (500 chars):\n{resp_rak.content[:500].decode()}")
        print(f"👤 User ID connecté: {rakib.id}")
        print(f"📑 Folio Buyer ID: {folio.buyer.id}")
        return

    print(f"🕵️ Rakib voit le folio {folio.id} au statut: {resp_rak.context['folio'].get_status_display()}")
    assert str(resp_rak.context['folio'].status) == 'STEP1_NOTARY_SELECTED'

    # Login Ousmane
    logged_ous = client_ousmane.login(username=ousmane_email, password="Ousmane2026")
    print(f"🔑 Login Ousmane: {'SUCCÈS' if logged_ous else 'ÉCHEC'}")
    
    url_ous = reverse('web_transaction_status', kwargs={'folio_id': folio.id})
    resp_ous = client_ousmane.get(url_ous, follow=True)
    print(f"📡 Response Ousmane: {resp_ous.status_code}")
    
    if resp_ous.status_code != 200:
        print(f"❌ Erreur: Ousmane n'a pas pu accéder à son dossier. Status: {resp_ous.status_code}")
        return

    print(f"🕵️ Ousmane voit le folio {folio.id} au statut: {resp_ous.context['folio'].get_status_display()}")
    assert str(resp_ous.context['folio'].status) == 'STEP1_NOTARY_SELECTED'

    # 4. ACTION DU NOTAIRE (Passer à l'Étape 3)
    client_notaire.login(username=notaire_email, password="Notaire2026")
    print("⚖️ Me Akoffodji met à jour le dossier vers l'étape 3 (Acte de Vente Signé)...")
    client_notaire.post(
        reverse('update_transaction_step', kwargs={'folio_id': folio.id}),
        {'next_step': 'STEP3_DEED_SIGNED'}
    )

    # 5. VÉRIFICATION DE LA SYNCHRONISATION (Étape 3)
    folio.refresh_from_db()
    
    # Re-check Rakib
    resp_rak2 = client_rakib.get(reverse('web_transaction_status', kwargs={'folio_id': folio.id}))
    print(f"🕵️ SYNC CHECK: Rakib voit maintenant: {resp_rak2.context['folio'].get_status_display()}")
    assert str(resp_rak2.context['folio'].status) == 'STEP3_DEED_SIGNED'

    # Re-check Ousmane
    resp_ous2 = client_ousmane.get(reverse('web_transaction_status', kwargs={'folio_id': folio.id}))
    print(f"🕵️ SYNC CHECK: Ousmane voit maintenant: {resp_ous2.context['folio'].get_status_display()}")
    assert str(resp_ous2.context['folio'].status) == 'STEP3_DEED_SIGNED'

    # 6. FINALISATION (Étape 6) ET CHANGEMENT DE PRÉPRIÉTAIRE
    print("⚖️ Me Akoffodji finalise la mutation (Étape 6)...")
    client_notaire.post(
        reverse('update_transaction_step', kwargs={'folio_id': folio.id}),
        {'next_step': 'STEP6_COMPLETED'}
    )

    folio.refresh_from_db()
    prop.refresh_from_db()

    print(f"🏁 Statut Final Folio: {folio.get_status_display()}")
    print(f"🏠 Nouveau Propriétaire Officiel de {prop.village}: {prop.owner_wallet.full_name} ({prop.owner_wallet.email})")

    assert str(folio.status) == 'STEP6_COMPLETED'
    assert prop.owner_wallet == rakib
    
    print("\n✅ TEST DE SYNCHRONISATION RÉUSSI À 100%. LES 3 PARTIES SONT BIEN CONNECTÉES AU MÊME DOSSIER.")

if __name__ == "__main__":
    try:
        test_three_party_synchronization()
    except Exception as e:
        print(f"❌ TEST ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
