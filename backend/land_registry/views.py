import json
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Count
from .models import Property, PropertyMedia, PropertyWitness, AuthorizedSurveyor
from identity.models import User
from consensus.models import ValidationRequest

# --- DASHBOARD VIEW (HTML) ---

def dashboard(request):
    """
    Tableau de bord principal pour l'administrateur / superviseur (Vision B2G).
    """
    total_properties = Property.objects.count()
    
    # Statistiques avancées (B2G)
    certified_count = sum(1 for p in Property.objects.all() if p.is_certified)
    active_surveyors_count = AuthorizedSurveyor.objects.filter(is_active=True).count()
    pending_surveyor_count = Property.objects.filter(status=Property.Status.PENDING_SURVEYOR).count()
    
    raw_stats = {s['status']: s['count'] for s in Property.objects.values('status').annotate(count=Count('status'))}
    properties_by_status = []
    for status_code, status_label in Property.Status.choices:
        properties_by_status.append({
            'status': status_code,
            'label': status_label,
            'count': raw_stats.get(status_code, 0)
        })
    
    total_users = User.objects.count()
    witnesses_count = PropertyWitness.objects.count() # On compte les enregistrements de témoins
    pending_validations = ValidationRequest.objects.filter(status=ValidationRequest.Status.OPEN).count()

    # Données pour la carte globale
    all_properties = Property.objects.all().select_related('surveyor')
    properties_json = []
    for p in all_properties:
        properties_json.append({
            'id': str(p.id),
            'lat': float(p.gps_centroid.get('lat', 0)),
            'lng': float(p.gps_centroid.get('lng', 0)),
            'status': p.status,
            'village': p.village or "N/A",
            'is_certified': p.is_certified
        })

    recent_properties = all_properties.order_by('-id')[:5]

    context = {
        'total_properties': total_properties,
        'properties_by_status': properties_by_status,
        'total_users': total_users,
        'witnesses_count': witnesses_count,
        'pending_validations': pending_validations,
        'certified_count': certified_count,
        'active_surveyors_count': active_surveyors_count,
        'pending_surveyor_count': pending_surveyor_count,
        'properties_json': properties_json,
        'recent_properties': recent_properties
    }
    return render(request, 'dashboard.html', context)

def user_dashboard(request, wallet):
    """
    Tableau de bord personnel pour un utilisateur.
    ROBUSTE : Priorise la session active si l'URL échoue.
    """
    try:
        identifier = wallet.lower().strip()
        user = None
        
        # 1. Essayer par UUID
        try:
            import uuid
            user_id = uuid.UUID(identifier)
            user = User.objects.get(id=user_id)
        except (ValueError, User.DoesNotExist):
            pass
            
        # 2. Essayer par wallet
        if not user:
            try:
                user = User.objects.get(wallet_address=identifier)
            except User.DoesNotExist:
                pass
                
        # 3. Essayer par email
        if not user:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        
        # ROBUSTESSE : Si l'utilisateur n'est pas trouvé via l'URL, 
        # mais qu'une session est active, on utilise l'utilisateur connecté.
        if not user and request.user.is_authenticated:
            print(f"⚠️ User not found via URL '{identifier}', falling back to session user: {request.user}")
            user = request.user
                
        if not user:
            return render(request, 'user_dashboard.html', {'error': 'Utilisateur non trouvé'})
        
        user_properties = Property.objects.filter(owner_wallet=user).annotate(media_count=Count('media'))
        
        context = {
            'user': user,
            'properties': user_properties,
            'total_assets': user_properties.count(),
        }
        return render(request, 'user_dashboard.html', context)
    except Exception as e:
        # Dernier recours : session active
        if request.user.is_authenticated:
             return redirect('user_dashboard', wallet=str(request.user.id))
        return render(request, 'user_dashboard.html', {'error': f'Erreur: {str(e)}'})
def web_add_property(request, wallet):
    """Vue pour ajouter une parcelle à un utilisateur existant."""
    try:
        identifier = wallet.lower().strip()
        user = None
        
        # 1. Essayer par UUID
        try:
            import uuid
            user_id = uuid.UUID(identifier)
            user = User.objects.get(id=user_id)
        except (ValueError, User.DoesNotExist):
            pass
            
        # 2. Essayer par wallet
        if not user:
            try:
                user = User.objects.get(wallet_address=identifier)
            except User.DoesNotExist:
                pass
                
        # 3. Essayer par email
        if not user:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        
        # ROBUSTESSE : Si l'utilisateur n'est pas trouvé via l'URL, 
        # mais qu'une session est active, on utilise l'utilisateur connecté.
        if not user and request.user.is_authenticated:
             user = request.user
                
        if not user:
            return redirect('web_login')
            
        return render(request, 'add_property.html', {'user': user})
    except Exception:
        if request.user.is_authenticated:
             return render(request, 'add_property.html', {'user': request.user})
        return redirect('web_login')

def web_properties(request):
    return render(request, 'properties.html')

def web_property_detail(request, pk):
    """Vue HTML détaillée pour une propriété spécifique."""
    try:
        prop = Property.objects.get(pk=pk)
        media = prop.media.all()
        return render(request, 'property_detail.html', {
            'property': prop,
            'media': media,
            'owner': prop.owner_wallet
        })
    except Property.DoesNotExist:
        return render(request, 'property_detail.html', {'error': 'Propriété non trouvée'})

def web_profile(request, wallet):
    """Vue HTML pour le profil utilisateur."""
    try:
        identifier = wallet.lower().strip()
        user = None
        
        # 1. Essayer par UUID
        try:
            import uuid
            user_id = uuid.UUID(identifier)
            user = User.objects.get(id=user_id)
        except:
            pass
            
        # 2. Essayer par wallet ou autre
        if not user:
            try:
                user = User.objects.get(wallet_address=identifier)
            except:
                pass
                
        # 3. Essayer par email
        if not user:
            try:
                 # Si n'est pas email, ça raise DB error
                 if '@' in identifier:
                    user = User.objects.get(email=identifier)
            except:
                pass

        # ROBUSTESSE
        if not user and request.user.is_authenticated:
            user = request.user

        if not user:
            return render(request, 'profile.html', {'error': 'Utilisateur non trouvé'})
            
        return render(request, 'profile.html', {'user': user})
    except Exception:
        if request.user.is_authenticated:
             return render(request, 'profile.html', {'user': request.user})
        return render(request, 'profile.html', {'error': 'Erreur interne'})

def web_register_user(request):
    """Vue pour l'inscription avec email/mot de passe."""
    if request.user.is_authenticated:
        return redirect('user_dashboard', wallet=str(request.user.id))
    return render(request, 'register.html')

def web_login(request):
    """Vue pour la connexion citoyenne."""
    if request.user.is_authenticated:
        return redirect('user_dashboard', wallet=str(request.user.id))
    return render(request, 'login.html')

def web_logout(request):
    """Vue pour la déconnexion."""
    from django.contrib.auth import logout
    logout(request)
    return redirect('web_login')

def web_password_reset(request):
    """Vue pour la réinitialisation de mot de passe."""
    return render(request, 'password_reset.html')

# --- API VIEWS (JSON) ---

@method_decorator(csrf_exempt, name='dispatch')
class PropertyListAPI(View):
    def get(self, request):
        properties = Property.objects.annotate(media_count=Count('media')).all()[:50]
        data = []
        for p in properties:
            owner_name = p.owner_wallet.full_name if p.owner_wallet.full_name else p.owner_wallet.wallet_address
            data.append({
                'id': str(p.id),
                'owner': owner_name,
                'status': p.status,
                'gps_centroid': p.gps_centroid,
                'media_count': p.media_count
            })
        return JsonResponse({'count': len(data), 'results': data})

    def post(self, request):
        try:
            if request.content_type.startswith('multipart/form-data') or request.content_type.startswith('application/x-www-form-urlencoded'):
                data = request.POST
                files = request.FILES.getlist('files')
                gps_centroid = json.loads(data.get('gps_centroid', '{"lat":0, "lng":0}'))
                gps_boundaries = json.loads(data.get('gps_boundaries', '[]'))
                owner_wallet = data.get('owner_wallet')
                owner_name = data.get('owner_name')
                birth_date = data.get('birth_date')
                user_country = data.get('user_country', 'Benin')
                district = data.get('district')
                village = data.get('village')
                surveyor_id = data.get('surveyor_id')
                surveyor_name = data.get('surveyor_name')
                area_sqm = data.get('area_sqm')
                area_cadastral = data.get('area_cadastral')
                country = data.get('country', 'Benin')
                witnesses_json = data.get('witnesses', '[]')
            else:
                body = json.loads(request.body)
                owner_wallet = body.get('owner_wallet')
                owner_name = body.get('owner_name')
                birth_date = body.get('birth_date')
                user_country = body.get('user_country', 'Benin')
                district = body.get('district')
                village = body.get('village')
                surveyor_id = body.get('surveyor_id')
                surveyor_name = body.get('surveyor_name')
                area_sqm = body.get('area_sqm')
                area_cadastral = body.get('area_cadastral')
                country = body.get('country', 'Benin')
                witnesses_json = json.dumps(body.get('witnesses', []))
                gps_centroid = body.get('gps_centroid', {'lat': 0, 'lng': 0})
                gps_boundaries = body.get('gps_boundaries', [])
                files = []

            # Si le wallet n'est pas fourni (cas de l'inscription), on le génère
            if not owner_wallet:
                if not owner_name or not birth_date:
                    return JsonResponse({'error': 'owner_name et birth_date requis pour la création de compte'}, status=400)
                
                # Génération d'un wallet déterministe simple (prefix + hash du nom + date)
                import hashlib
                raw_id = f"{owner_name}{birth_date}".lower().strip()
                fingerprint = hashlib.sha256(raw_id.encode()).hexdigest()[:10]
                owner_wallet = f"0xilot_{fingerprint}"
            else:
                owner_wallet = owner_wallet.lower().strip()
            
            if not owner_name:
                return JsonResponse({'error': 'owner_name requis'}, status=400)

            # 1. Validation Géométrique - Ordre et Convexité
            if len(gps_boundaries) < 3:
                return JsonResponse({'error': 'La parcelle doit avoir au moins 3 bornes.'}, status=400)

            # Vérification basique des coordonnées
            for pt in gps_boundaries:
                if not (-90 <= pt['lat'] <= 90) or not (-180 <= pt['lng'] <= 180):
                    return JsonResponse({'error': 'Coordonnées GPS invalides.'}, status=400)

            # Vérification Convexité
            def cross_product(o, a, b):
                return (a['lng'] - o['lng']) * (b['lat'] - o['lat']) - (a['lat'] - o['lat']) * (b['lng'] - o['lng'])

            n = len(gps_boundaries)
            cp_signs = []
            for i in range(n):
                p1 = gps_boundaries[i]
                p2 = gps_boundaries[(i + 1) % n]
                p3 = gps_boundaries[(i + 2) % n]
                cp = cross_product(p1, p2, p3)
                if cp != 0:
                    cp_signs.append(cp > 0)
            
            # Si tous les produits vectoriels n'ont pas le même signe (sauf 0), le polygone n'est pas convexe
            if not (all(cp_signs) or not any(cp_signs)):
                 return JsonResponse({'error': 'La forme de la parcelle est invalide (non convexe). Vérifiez l\'ordre des points.'}, status=400)

            # Validation Distance vs Centroid (Pour éviter des points éparpillés au hasard)
            # On tolère une "grande" parcelle mais pas des points à l'autre bout du pays
            # Max diag distance approx 5km (0.05 degrés d'écart environ)
            c_lat = float(gps_centroid.get('lat') or 0)
            c_lng = float(gps_centroid.get('lng') or 0)
            
            for pt in gps_boundaries:
                dist_lat = abs(pt['lat'] - c_lat)
                dist_lng = abs(pt['lng'] - c_lng)
                if dist_lat > 0.05 or dist_lng > 0.05: # Approx 5.5km
                     return JsonResponse({'error': 'Les bornes sont trop éloignées du point central (Max 5km).'}, status=400)

            # 2. Vérification des Doublons (Coordonnées du Centroide)
            existing = Property.objects.filter(
                gps_centroid__lat__gte=c_lat-0.0001, 
                gps_centroid__lat__lte=c_lat+0.0001,
                gps_centroid__lng__gte=c_lng-0.0001,
                gps_centroid__lng__lte=c_lng+0.0001
            ).exists()
            
            if existing:
                return JsonResponse({'error': 'Une parcelle est déjà enregistrée à ces coordonnées.'}, status=409)

            # Validation du nom
            import re
            if not re.match(r"^[a-zA-Z\s\.\-]+$", owner_name) or len(owner_name) < 3:
                return JsonResponse({'error': 'Nom invalide'}, status=400)
            
            owner, _ = User.objects.get_or_create(wallet_address=owner_wallet)
            owner.full_name = owner_name
            if birth_date:
                owner.birth_date = birth_date
            
            # Nouvelles informations d'identité
            owner.country = user_country
            owner.district = district
            owner.village = village
            
            owner.save()
            
            # Génération d'un ID blockchain aléatoire (simulé)
            import random
            simulated_on_chain_id = str(random.randint(100000, 999999))

            prop = Property.objects.create(
                owner_wallet=owner,
                gps_centroid=gps_centroid,
                gps_boundaries=gps_boundaries,
                country=country,
                district=district,
                village=village,
                surveyor_id=surveyor_id if surveyor_id else None,
                surveyor_name=surveyor_name,
                area_sqm=float(area_sqm) if area_sqm else None,
                area_cadastral=area_cadastral,
                on_chain_id=simulated_on_chain_id,
                status=Property.Status.PENDING_SURVEYOR if surveyor_id else Property.Status.DRAFT
            )
            
            # --- SIMULATION ENVOI EMAIL ---
            if prop.surveyor:
                # Dans un vrai projet : from django.core.mail import send_mail
                print(f"🔔 [EMAIL SIMULATION] Destinataire: {prop.surveyor.email}")
                print(f"Objet: Nouvelle parcelle à attester - ID: {prop.id}")
                print(f"Détails: L'utilisateur {owner.full_name} a déclaré une parcelle à {prop.village}.")

            # Sauvegarde des Témoins
            import hashlib
            witnesses_data = json.loads(witnesses_json)
            for i, w_data in enumerate(witnesses_data):
                idx = i + 1
                w_file = request.FILES.get(f'witness_id_{idx}')
                fake_w_cid = ""
                if w_file:
                    w_content = w_file.read()
                    w_file.seek(0)
                    fake_w_cid = "Qm" + hashlib.sha256(w_content).hexdigest()[:44]
                
                witness_obj = PropertyWitness.objects.create(
                    property=prop,
                    last_name=w_data.get('last_name'),
                    first_name=w_data.get('first_name'),
                    birth_date=w_data.get('birth_date'),
                    gender=w_data.get('gender'),
                    phone=w_data.get('phone'),
                    email=w_data.get('email'),
                    id_card_photo=w_file,
                    ipfs_cid=fake_w_cid
                )

                # --- SIMULATION ENVOI EMAIL TÉMOIN ---
                if witness_obj.email:
                    print(f"👥 [EMAIL SIMULATION TÉMOIN] Destinataire: {witness_obj.email}")
                    print(f"Objet: Témoignage requis pour iLôt Foncier - {prop.id}")
                    print(f"Détails: Bonjour {witness_obj.first_name}, vous avez été cité comme témoin pour la parcelle de {owner.full_name}.")

            # Sauvegarde des médias
            import hashlib
            for f in files:
                # Calcul du CID simulé (Qm + hash du contenu)
                content = f.read()
                f.seek(0) # Reset position for saving
                fake_cid = "Qm" + hashlib.sha256(content).hexdigest()[:44]
                
                m_type = PropertyMedia.MediaType.OTHER_MEDIA
                if f.content_type.startswith('image/'): 
                    m_type = PropertyMedia.MediaType.PHOTO_LAND
                elif f.content_type.startswith('video/'): 
                    m_type = PropertyMedia.MediaType.VIDEO_DRONE
                elif f.content_type == 'application/pdf': 
                    m_type = PropertyMedia.MediaType.LEGAL_DOC

                PropertyMedia.objects.create(
                    property=prop, 
                    file=f,
                    ipfs_cid=fake_cid, 
                    media_type=m_type
                )

            return JsonResponse({'id': str(prop.id), 'status': prop.status, 'wallet_address': owner_wallet}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PropertyDetailAPI(View):
    """
    API Endpoint: /api/properties/<uuid>/
    GET: Détails d'une propriété
    """
    def get(self, request, pk):
        try:
            p = Property.objects.get(pk=pk)
            data = {
                'id': str(p.id),
                'owner': p.owner_wallet.wallet_address,
                'status': p.status,
                'gps_centroid': p.gps_centroid,
                'gps_boundaries': p.gps_boundaries,
                'on_chain_id': p.on_chain_id
            }
            return JsonResponse(data)
        except Property.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)


def web_logout(request):
    """Vue de déconnexion"""
    logout(request)
    return redirect('web_login')
