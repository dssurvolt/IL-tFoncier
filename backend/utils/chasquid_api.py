from django.core.mail import send_mail
from django.conf import settings

class EmailNotifier:
    """
    Gestionnaire d'envoi d'emails utilisant le système natif de Django.
    """
    
    @staticmethod
    def send_witness_invitation(witness_name, witness_email, owner_name, property_id, validation_link):
        """
        Envoie une invitation à un témoin via Django send_mail.
        """
        subject = f"iLôt Foncier - Témoignage requis pour {owner_name}"
        
        message = f"""
Bonjour {witness_name},

L'utilisateur {owner_name} vous a cité comme témoin pour sa déclaration de parcelle (ID: {property_id[:8]}) sur iLôt Foncier.

Votre confirmation est essentielle pour sécuriser ce patrimoine au sein de la communauté.

Veuillez cliquer sur le lien ci-dessous pour confirmer votre témoignage :
{validation_link}

Si vous ne connaissez pas cette personne ou si cette demande vous semble erronée, vous pouvez ignorer cet email ou signaler une fraude via le lien.

Cordialement,
L'équipe iLôt Foncier
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[witness_email],
                fail_silently=False,
            )
            print(f"📧 [Django Email] Envoyé avec succès à {witness_email}")
            return True
        except Exception as e:
            print(f"❌ [Django Email] Erreur d'envoi à {witness_email} : {e}")
            return False
