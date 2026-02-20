from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import USSDSession, User
from land_registry.models import Property
from consensus.models import ValidationRequest, WitnessVote

def web_ussd(request):
    """Vue HTML pour le simulateur USSD."""
    return render(request, 'ussd_simulator.html')

@method_decorator(csrf_exempt, name='dispatch')
class USSDGateway(View):
    """
    Gateway USSD Avancée (State Machine).
    Gère: Enregistrement, Validation, Consultation Compte.
    """
    def post(self, request):
        session_id = request.POST.get('sessionId')
        phone_number = self.normalize_phone(request.POST.get('phoneNumber', ''))
        text = request.POST.get('text', '')

        # Récupérer/Créer session
        session, created = USSDSession.objects.get_or_create(
            session_id=session_id,
            defaults={'phone_number': phone_number, 'current_menu': 'MAIN', 'input_buffer': {}}
        )

        # Parsing de l'input
        user_input = text.split('*')[-1] if text else ''
        
        if text == '':
            session.current_menu = 'MAIN'
            session.save()

        try:
            response = self.state_machine(session, user_input, phone_number)
        except Exception as e:
            import traceback
            traceback.print_exc()
            response = f"END Erreur systeme: {str(e)}"
            
        return HttpResponse(response, content_type="text/plain")

    def normalize_phone(self, phone):
        """Assure que le numéro est au format +[code][numero] sans doublons."""
        phone = phone.strip().replace(' ', '')
        if not phone: return "unknown"
        
        # Si ça commence déjà par +, on ne touche à rien
        if phone.startswith('+'):
            return phone
            
        # Si ça commence par 00, on remplace par +
        if phone.startswith('00'):
            return '+' + phone[2:]
            
        # Si le numéro commence par 229 (Bénin) mais sans +, on ajoute juste +
        if phone.startswith('229') and len(phone) >= 11:
            return '+' + phone
            
        # Par défaut, on assume le Bénin (+229) et on ajoute le préfixe
        return '+229' + phone

    def state_machine(self, session, user_input, phone_number):
        """Cœur logique du USSD"""
        menu = session.current_menu
        
        # --- MENU PRINCIPAL ---
        if menu == 'MAIN':
            response = "CON Bienvenue sur iLot Foncier\n"
            response += "1. Enregistrer un terrain\n"
            response += "2. Valider un terrain (Voisin)\n"
            response += "3. Mon Compte\n"
            response += "4. Aide"
            session.current_menu = 'WAITING_MAIN_CHOICE'
            session.save()
            return response

        # --- ROUTAGE PRINCIPAL ---
        if menu == 'WAITING_MAIN_CHOICE':
            if user_input == '1':
                session.current_menu = 'REG_ASK_NAME'
                session.save()
                return "CON Entrez le Nom et Prenom du proprietaire :"
            elif user_input == '2':
                session.current_menu = 'VAL_ASK_ID'
                session.save()
                return "CON Entrez l'ID du terrain a valider (ex: 8 char):"
            elif user_input == '3':
                # Logique Mon Compte
                user, _ = User.objects.get_or_create(wallet_address=f"tel:{phone_number}")
                response = f"END -- Mon Profil --\n"
                response += f"Role: {user.role}\n"
                response += f"Reputation: {user.reputation_score}/100\n"
                response += f"Terrains: {Property.objects.filter(owner_wallet=user).count()}"
                session.delete() # Fin de session
                return response
            elif user_input == '4':
                return "END iLot Foncier securise vos terres grace a la blockchain et vos voisins.\nPlus d'infos: www.ilot-foncier.africa"
            else:
                return "END Choix invalide."

        # --- FLUX ENREGISTREMENT ---
        if menu == 'REG_ASK_NAME':
            # Validation du nom: Lettres, espaces, points, tirets uniquement
            import re
            if not re.match(r"^[a-zA-Z\s\.\-]+$", user_input) or len(user_input) < 3:
                return "CON Nom invalide (Lettres, espaces, . - uniquement).\nReessayez :"
            
            session.input_buffer['full_name'] = user_input
            session.current_menu = 'REG_ASK_LAT'
            session.save()
            return "CON Entrez la Latitude (Format DD, ex: 6.36) :"

        if menu == 'REG_ASK_LAT':
            try:
                lat = float(user_input)
                if not (-90 <= lat <= 90): raise ValueError()
            except ValueError:
                return "CON Latitude invalide (-90 a 90).\nReessayez :"
                
            session.input_buffer['lat'] = user_input
            session.current_menu = 'REG_ASK_LNG'
            session.save()
            return "CON Entrez la Longitude (Format DD, ex: 2.42) :"

        if menu == 'REG_ASK_LNG':
            try:
                lng = float(user_input)
                if not (-180 <= lng <= 180): raise ValueError()
            except ValueError:
                return "CON Longitude invalide (-180 a 180).\nReessayez :"

            session.input_buffer['lng'] = user_input
            session.current_menu = 'REG_ASK_SIZE'
            session.save()
            return "CON Entrez la superficie approximative (en m2) :"
            
        if menu == 'REG_ASK_SIZE':
            full_name = session.input_buffer.get('full_name', 'Inconnu')
            lat_raw = session.input_buffer.get('lat', '0')
            lng_raw = session.input_buffer.get('lng', '0')
            size = user_input
            
            # Conversion sécurisée en float
            try:
                lat = float(lat_raw)
                lng = float(lng_raw)
            except (ValueError, TypeError):
                lat, lng = 0.0, 0.0

            # Création/Mise à jour de l'utilisateur avec son nom réel
            user, created = User.objects.get_or_create(
                wallet_address=f"tel:{phone_number}",
                defaults={'full_name': full_name}
            )
            if not created and full_name != 'Inconnu':
                user.full_name = full_name
                user.save()

            # Création de la propriété
            prop = Property.objects.create(
                owner_wallet=user,
                gps_centroid={'lat': lat, 'lng': lng, 'source': 'USSD'},
                gps_boundaries=[],
                status=Property.Status.DRAFT
            )
            
            # Simulation d'envoi de lien SMS pour les médias
            upload_link = f"ilot.africa/m/{str(prop.id)[:8]}"
            
            response = f"END Terrain enregistre (ID: {str(prop.id)[:8]}).\n"
            response += f"IMPORTANT: Cliquez sur le lien recu par SMS pour uploader vos photos/videos: {upload_link}"
            
            session.delete()
            return response

        # --- FLUX VALIDATION (TÉMOIN) ---
        if menu == 'VAL_ASK_ID':
            try:
                props = Property.objects.filter(id__startswith=user_input)
                if not props.exists():
                    return "END Terrain introuvable. Verifiez l'ID."
                
                prop = props.first()
                session.input_buffer['target_prop_id'] = str(prop.id)
                session.current_menu = 'VAL_ASK_NAME'
                session.save()
                return "CON Entrez votre Nom et Prenoms complets (Responsabilite Juridique) :"
            except Exception:
                return "END Erreur technique."

        if menu == 'VAL_ASK_NAME':
            # Validation du nom (pas de chiffres)
            import re
            if not re.match(r"^[a-zA-Z\s\.\-]+$", user_input) or len(user_input) < 3:
                return "CON Nom invalide. Entrez votre Nom et Prenoms (Lettres uniquement) :"
            
            session.input_buffer['witness_name'] = user_input
            session.current_menu = 'VAL_ASK_BIRTH'
            session.save()
            return "CON Entrez votre Date de Naissance (JJMMAAAA) :"

        if menu == 'VAL_ASK_BIRTH':
            # Validation date simple (8 chiffres)
            if not user_input.isdigit() or len(user_input) != 8:
                return "CON Format invalide. Entrez votre Date de Naissance (JJMMAAAA) :"
            
            # Conversion pour le stockage (JJMMAAAA -> YYYY-MM-DD)
            formatted_date = f"{user_input[4:]}-{user_input[2:4]}-{user_input[:2]}"
            session.input_buffer['witness_birth_date'] = formatted_date
            session.current_menu = 'VAL_ASK_DOC'
            session.save()
            return "CON Entrez Numero Passeport ou ID National :"

        if menu == 'VAL_ASK_DOC':
            if len(user_input) < 5:
                return "CON Numero trop court. Entrez Numero Passeport ou ID National :"
            
            session.input_buffer['witness_id_number'] = user_input
            session.current_menu = 'VAL_CONFIRM'
            session.save()
            
            prop = Property.objects.get(id=session.input_buffer['target_prop_id'])
            owner_display = prop.owner_wallet.full_name if prop.owner_wallet.full_name else prop.owner_wallet.wallet_address[:8]
            return f"CON Confirmez-vous l'existence du terrain de {owner_display} ?\n1. OUI (Je certifie)\n2. NON (Signalement)"

        if menu == 'VAL_CONFIRM':
            prop_id = session.input_buffer.get('target_prop_id')
            witness_name = session.input_buffer.get('witness_name')
            witness_birth = session.input_buffer.get('witness_birth_date')
            witness_id = session.input_buffer.get('witness_id_number')
            
            if user_input == '1':
                self._record_vote(prop_id, phone_number, witness_name, witness_birth, witness_id, True)
                return "END Vote certifie enregistre.\nMerci pour votre civisme !"
            elif user_input == '2':
                self._record_vote(prop_id, phone_number, witness_name, witness_birth, witness_id, False)
                return "END Signalement de fraude enregistre.\nUne enquete sera menee."
            else:
                return "END Operation annulee."

        return "END Erreur inconnue."

    def _record_vote(self, prop_id, phone_number, witness_name, witness_birth, witness_id, vote_result):
        """Helper pour enregistrer le vote avec identité légale universelle"""
        witness_user, _ = User.objects.get_or_create(
            wallet_address=f"tel:{phone_number}", 
            defaults={'role': User.Role.WITNESS, 'full_name': witness_name}
        )
        prop = Property.objects.get(id=prop_id)
        
        # Trouver ou créer une ValidationRequest ouverte
        val_req = ValidationRequest.objects.filter(property=prop, status=ValidationRequest.Status.OPEN).first()
        if not val_req:
            val_req = ValidationRequest.objects.create(
                property=prop,
                requester_wallet=prop.owner_wallet.wallet_address,
                gps_at_request={'lat': 0, 'lng': 0},
                status=ValidationRequest.Status.OPEN
            )
            
        WitnessVote.objects.create(
            request_id=val_req.id,
            witness_full_name=witness_name,
            witness_birth_date=witness_birth,
            witness_phone=phone_number,
            witness_id_number=witness_id,
            witness_wallet=witness_user,
            witness_gps={'lat': 0, 'lng': 0, 'source': 'USSD'},
            vote_result=vote_result,
            signature=f"USSD_HASH_{uuid.uuid4().hex[:8]}"
        )
