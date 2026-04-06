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
from marketplace.models import Listing, ChatRoom, ChatMessage, Notification

def run_full_validation():
    print("🚀 DÉBUT DE LA VÉRIFICATION COMPLÈTE DU SYSTÈME (E2E) 🚀")
    
    # 1. SETUP DES ACTEURS
    buyer_email = "rakib.sobabe@ilot.bj"
    seller_email = "ousmane.alfa@exemple.com"
    notary_email = "jp.akoffodji@notariat.bj"
    
    password = "Rakib2026Password" # On utilise le même pour tous dans setup_rakib_scenario
    # Note: Dans setup_rakib_scenario j'ai mis Ousmane2026Password etc...
    # Mettons à jour pour être sur
    
    buyer = User.objects.get(email=buyer_email)
    seller = User.objects.get(email=seller_email)
    notary_u = User.objects.get(email=notary_email)
    notary_p = Notary.objects.get(user=notary_u)

    c_buyer = Client()
    c_seller = Client()
    c_notary = Client()

    # --- PHASE 1 : MARKETPLACE & CHAT ---
    print("\n--- PHASE 1 : MARKETPLACE & CHAT ---")
    
    # Login Buyer
    success = c_buyer.login(username=buyer_email, password="Rakib2026Password")
    print(f"🔑 Tentative de connexion (Rakib) : {'SUCCÈS' if success else 'ÉCHEC'}")
    assert success, "Login Rakib a échoué. Vérifiez le mot de passe dans setup_rakib_scenario.py."
    
    # Voir la Marketplace
    resp = c_buyer.get(reverse('web_marketplace'))
    assert resp.status_code == 200
    print("✅ Marketplace accessible.")

    # Nettoyage préventif
    ChatRoom.objects.filter(buyer=buyer).delete()

    # Démarrer une discussion
    listing = Listing.objects.filter(property__village="Lot 405 - Cadjèhoun", status=Listing.Status.ACTIVE).first()
    if not listing:
        print("❌ L'annonce 'Lot 405 - Cadjèhoun' n'est pas disponible pour le test !")
        # Essayons n'importe quelle annonce dont Rakib n'est pas le proprio
        listing = Listing.objects.exclude(property__owner_wallet=buyer).filter(status=Listing.Status.ACTIVE).first()

    if not listing:
         print("❌ Aucune annonce valide (non-proprio) trouvée !")
         return
    
    print(f"💬 Rakib démarre une discussion pour : {listing.property.village} (ID: {listing.id})")
    url_start = reverse('web_start_chat', kwargs={'listing_id': listing.id})
    print(f"🔗 GET {url_start}")
    resp = c_buyer.get(url_start, follow=True)
    
    print(f"📑 Redirection finale : {resp.request['PATH_INFO']}")
    assert resp.status_code == 200
    
    try:
        room = ChatRoom.objects.get(buyer=buyer, listing=listing)
        print(f"✅ Salon de discussion créé (ID: {room.id})")
    except ChatRoom.DoesNotExist:
        print(f"❌ ÉCHEC : Le salon n'a pas été créé par la vue web_start_chat.")
        print(f"CONTEXTE : Buyer ID={buyer.id}, Listing ID={listing.id}")
        # On regarde si un salon existe avec n'importe qui
        count = ChatRoom.objects.all().count()
        print(f"Nombre total de salons en DB : {count}")
        raise

    # Envoyer un message (via API)
    from django.test import RequestFactory
    factory = RequestFactory()
    msg_data = {'room_id': str(room.id), 'content': "Bonjour, je suis intéressé !"}
    resp = c_buyer.post(reverse('api_chat_send'), data=msg_data)
    assert resp.status_code == 201
    print("✅ Premier message envoyé par Rakib.")

    # Vendeur répond
    c_seller.login(username=seller_email, password="Ousmane2026Password")
    msg_data_reply = {'room_id': str(room.id), 'content': "Bonjour Rakib, la parcelle est disponible."}
    resp = c_seller.post(reverse('api_chat_send'), data=msg_data_reply)
    assert resp.status_code == 201
    print("✅ Réponse envoyée par Ousmane.")

    # --- PHASE 2 : TRANSACTION NOTARIÉE ---
    print("\n--- PHASE 2 : TRANSACTION NOTARIÉE ---")
    
    # Rakib choisit le notaire
    print(f"⚖️ Rakib choisit Me {notary_p.name}...")
    resp = c_buyer.get(reverse('web_start_transaction', kwargs={
        'property_id': listing.property.id,
        'notary_id': notary_p.id
    }), follow=True)
    assert resp.status_code == 200
    
    folio = TransactionFolio.objects.get(property=listing.property, buyer=buyer, status='STEP1_NOTARY_SELECTED')
    print(f"✅ Folio ouvert à l'étape 1 (ID: {folio.id})")

    # Sync Check: Vendeur voit le dossier
    resp = c_seller.get(reverse('web_transaction_status', kwargs={'folio_id': folio.id}))
    assert resp.status_code == 200
    print("✅ Ousmane (Vendeur) a bien accès au suivi de la transaction.")

    # Notaire valide l'étape 2 (ID)
    c_notary.login(username=notary_email, password="Notaire2026Password")
    print("🖋️ Le notaire valide les identités...")
    c_notary.post(reverse('update_transaction_step', kwargs={'folio_id': folio.id}), {'next_step': 'STEP2_ID_VERIFIED'})
    
    folio.refresh_from_db()
    assert folio.status == 'STEP2_ID_VERIFIED'
    print("✅ Étape 2 validée.")

    # Notaire finalise la mutation (Étape 6)
    print("🏁 Le notaire finalise la mutation (Étape 6)...")
    c_notary.post(reverse('update_transaction_step', kwargs={'folio_id': folio.id}), {'next_step': 'STEP6_COMPLETED'})
    
    folio.refresh_from_db()
    assert folio.status == 'STEP6_COMPLETED'
    
    # Vérification Propriété
    prop = listing.property
    prop.refresh_from_db()
    print(f"🏠 Nouveau propriétaire de la parcelle : {prop.owner_wallet.full_name}")
    assert prop.owner_wallet == buyer
    print("✅ Transfert de propriété Blockchain validé.")

    # Vérification Marketplace (Annonce vendue)
    listing.refresh_from_db()
    print(f"📢 État de l'annonce : {listing.get_status_display()}")
    assert listing.status == Listing.Status.SOLD
    print("✅ Annonce marquée comme VENDUE sur la Marketplace.")

    print("\n🏆 VÉRIFICATION COMPLÈTE RÉUSSIE : 100% FONCTIONNEL 🏆")

if __name__ == "__main__":
    try:
        run_full_validation()
    except Exception as e:
        print(f"❌ ÉCHEC DE LA VÉRIFICATION : {e}")
        import traceback
        traceback.print_exc()
