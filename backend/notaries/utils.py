import json
from django.core.mail import send_mail
from django.conf import settings
from marketplace.models import Notification
from identity.models import User

def notify_transaction_update(folio):
    """
    Envoie des notifications (Email/SMS simulé + In-app) lors d'un changement d'étape.
    """
    status_label = folio.get_status_display()
    property_village = folio.property.village or "votre terrain"
    
    # 1. Préparation des messages
    messages_map = {
        'STEP2_ID_VERIFIED': {
            'title': "Identités confirmées",
            'body': f"Le notaire a validé la présence physique des parties pour {property_village}. Le dossier avance !",
        },
        'STEP3_DEED_SIGNED': {
            'title': "Acte de vente signé",
            'body': f"L'acte de vente pour {property_village} a été signé à l'étude. Prochaine étape : dépôt ANDF.",
        },
        'STEP4_ANDF_DEPOSITED': {
            'title': "Dépôt ANDF effectué",
            'body': f"Votre dossier a été déposé à l'ANDF (N° {folio.andf_dossier_number}). La mutation est en cours.",
        },
        'STEP5_TITLE_MODIFIED': {
            'title': "Titre modifié",
            'body': f"Bonne nouvelle ! L'ANDF a mis à jour le titre de propriété pour {property_village}.",
        },
        'STEP6_COMPLETED': {
            'title': "Transaction terminée 🌿",
            'body': f"Félicitations ! La transaction pour {property_village} est terminée. Votre titre est disponible.",
        },
        'CANCELLED': {
            'title': "Transaction annulée ❌",
            'body': f"Le dossier de transaction pour {property_village} a été annulé par le notaire.",
        }
    }

    if folio.status not in messages_map:
        return

    msg_data = messages_map[folio.status]
    
    # 2. Notification In-App (Dashboard) pour l'acheteur et le vendeur
    for party in [folio.buyer, folio.seller]:
        Notification.objects.create(
            user_wallet=party,
            type='TRANSACTION_UPDATE',
            payload={
                'title': msg_data['title'],
                'message': msg_data['body'],
                'folio_id': str(folio.id),
                'status': folio.status
            }
        )

    # 3. Simulation Email (Backend console par défaut dans settings)
    # Dans un cas réel, on utiliserait un service comme SendGrid ou Mailjet
    subject = f"iLôt Foncier : {msg_data['title']}"
    emails = [folio.buyer.email, folio.seller.email]
    
    try:
        send_mail(
            subject,
            msg_data['body'],
            settings.DEFAULT_FROM_EMAIL,
            emails,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Erreur envoi email: {e}")

    # 4. Simulation SMS (Log console)
    # Dans un cas réel, on appellerait une API comme Twilio ou un gateway local
    for party in [folio.buyer, folio.seller]:
        if party.phone_hash: # Si on a un numéro (hashé ici pour la démo)
            print(f"--- SIMULATION SMS à {party.email} ---")
            print(f"SMS: {msg_data['body']}")
            print("---------------------------------------")
