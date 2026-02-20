import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Listing
from land_registry.models import Property
from identity.models import User

def web_marketplace(request):
    """Vue HTML pour la Marketplace citoyenne."""
    listings = Listing.objects.filter(status=Listing.Status.ACTIVE).select_related('property', 'property__owner_wallet')
    
    # Préparation des données pour la carte JS (Sécurisée via json_script)
    listings_data = []
    for l in listings:
        listings_data.append({
            'id': str(l.property.id), # On utilise l'ID de la propriété pour le lien technique
            'lat': float(l.property.gps_centroid.get('lat', 0)),
            'lng': float(l.property.gps_centroid.get('lng', 0)),
            'price_fiat': f"{l.price_fiat:,}",
            'village': l.property.village or "Parcelle iLôt",
            'is_certified': l.property.is_certified
        })
        
    return render(request, 'marketplace.html', {
        'listings': listings,
        'listings_json': listings_data
    })

def web_create_listing(request, property_id):
    """Vue HTML pour mettre un terrain en vente."""
    try:
        prop = Property.objects.get(id=property_id)
        
        # Sécurité : Seul le propriétaire peut voir ce formulaire
        if request.user.is_authenticated and prop.owner_wallet != request.user:
            return redirect('login_home')
            
        return render(request, 'create_listing.html', {
            'property': prop,
            'user': request.user if request.user.is_authenticated else prop.owner_wallet
        })
    except Property.DoesNotExist:
        return redirect('web_marketplace')

@method_decorator(csrf_exempt, name='dispatch')
class ListingListAPI(View):
    """
    API Endpoint: /api/marketplace/listings/
    GET: Liste les terrains à vendre
    POST: Mettre un terrain en vente
    """
    def get(self, request):
        listings = Listing.objects.filter(status=Listing.Status.ACTIVE)
        data = []
        for l in listings:
            data.append({
                'id': str(l.id),
                'property_id': str(l.property.id),
                'price_fiat': str(l.price_fiat),
                'price_crypto': str(l.price_crypto),
                'seller': l.property.owner_wallet.wallet_address
            })
        return JsonResponse({'count': len(data), 'results': data})

    def post(self, request):
        try:
            body = json.loads(request.body)
            property_id = body.get('property_id')
            seller_wallet = body.get('seller_wallet')
            price_fiat = body.get('price_fiat')
            price_crypto = body.get('price_crypto')

            # 1. Vérifier l'existence de la propriété
            try:
                prop = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                return JsonResponse({'error': 'Property not found'}, status=404)

            # 2. RÈGLE MÉTIER : Seules les propriétés validées ou en attestation peuvent être listées
            if prop.status not in [Property.Status.ON_CHAIN, Property.Status.PENDING_SURVEYOR]:
                return JsonResponse({'error': 'Only validated or pending surveyor properties can be listed for sale'}, status=400)

            # 3. RÈGLE MÉTIER : Le vendeur doit être le propriétaire
            if prop.owner_wallet.wallet_address != seller_wallet:
                return JsonResponse({'error': 'Only the owner can list this property'}, status=403)
            
            # 4. Vérifier si une offre active existe déjà
            if Listing.objects.filter(property=prop, status=Listing.Status.ACTIVE).exists():
                return JsonResponse({'error': 'Property is already listed for sale'}, status=400)

            # 5. Création de l'offre
            listing = Listing.objects.create(
                property=prop,
                price_fiat=price_fiat,
                price_crypto=price_crypto,
                status=Listing.Status.ACTIVE
            )
            return JsonResponse({'id': str(listing.id), 'status': 'ACTIVE'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
