import os
import django
import uuid
from django.test import Client, RequestFactory
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from land_registry.models import Property, PropertyWitness
from consensus.models import ValidationRequest, WitnessVote
from identity.models import User

def test_witness_full_flow():
    print("\n--- TEST: Flux Complet de Validation Témoin ---\n")
    
    # 1. Setup Data
    unique_id = uuid.uuid4().hex[:8]
    owner = User.objects.create(
        wallet_address=f"0x{uuid.uuid4().hex[:40]}", 
        full_name="Test Owner",
        email=f"owner_{unique_id}@test.com"
    )
    prop = Property.objects.create(
        owner_wallet=owner,
        village="Village Test",
        district="District Test",
        gps_centroid={"lat": 6.36, "lng": 2.42},
        gps_boundaries=[],
        status=Property.Status.DRAFT,
        area_sqm=500
    )
    
    # Create 3 witnesses
    w1 = PropertyWitness.objects.create(property=prop, first_name="T1", last_name="W1", phone="111", email="w1@test.com", birth_date="1990-01-01")
    w2 = PropertyWitness.objects.create(property=prop, first_name="T2", last_name="W2", phone="222", email="w2@test.com", birth_date="1990-01-01")
    w3 = PropertyWitness.objects.create(property=prop, first_name="T3", last_name="W3", phone="333", email="w3@test.com", birth_date="1990-01-01")
    
    # Initiate Validation
    val_req = ValidationRequest.objects.create(
        property=prop,
        requester_wallet=owner.wallet_address,
        gps_at_request={"lat": 6.36, "lng": 2.42},
        status=ValidationRequest.Status.OPEN
    )
    prop.status = Property.Status.VALIDATING
    prop.save()
    
    c = Client()
    
    # --- TEST 1: Premier témoin valide ---
    print("Testing Vote 1 (T1)...")
    url = f"/validation/witness/?req={val_req.id}&witness={w1.id}"
    response = c.post(url, {'vote': 'yes', 'id_number': 'ID123'})
    
    assert response.status_code == 200
    assert "Merci ! Votre témoignage a été enregistré" in response.content.decode()
    
    w1.refresh_from_db()
    assert w1.is_confirmed is True
    assert WitnessVote.objects.filter(request=val_req, witness_phone="111").exists()
    
    val_req.refresh_from_db()
    assert val_req.status == ValidationRequest.Status.OPEN
    prop.refresh_from_db()
    assert prop.status == Property.Status.VALIDATING
    print("✅ Vote 1 réussi.")

    # --- TEST 2: Vote en double ---
    print("Testing Duplicate Vote (T1)...")
    response = c.post(url, {'vote': 'yes', 'id_number': 'ID123'})
    assert "Vous avez déjà validé ce témoignage" in response.content.decode()
    print("✅ Détection de doublon réussie.")

    # --- TEST 3: Deuxième témoin valide ---
    print("Testing Vote 2 (T2)...")
    url2 = f"/validation/witness/?req={val_req.id}&witness={w2.id}"
    c.post(url2, {'vote': 'yes', 'id_number': 'ID456'})
    w2.refresh_from_db()
    assert w2.is_confirmed is True
    print("✅ Vote 2 réussi.")

    # --- TEST 4: Troisième témoin (Consensus atteint) ---
    print("Testing Final Vote (T3) -> Consensus...")
    url3 = f"/validation/witness/?req={val_req.id}&witness={w3.id}"
    response = c.post(url3, {'vote': 'yes', 'id_number': 'ID789'})
    
    assert "Le consensus est maintenant atteint" in response.content.decode()
    
    val_req.refresh_from_db()
    assert val_req.status == ValidationRequest.Status.COMPLETED
    
    prop.refresh_from_db()
    assert prop.status == Property.Status.ON_CHAIN
    print("✅ Consensus atteint et statut ON_CHAIN mis à jour.")

    # --- TEST 5: Lien invalide ---
    print("Testing Invalid Link...")
    url_bad = f"/validation/witness/?req={val_req.id}&witness={uuid.uuid4()}"
    response = c.get(url_bad)
    assert response.status_code == 404
    print("✅ 404 sur témoin inconnu réussi.")

    print("\n--- TOUS LES TESTS SONT PASSÉS ! ---")

if __name__ == "__main__":
    test_witness_full_flow()
    # Cleanup (optional in sqlite test db usually, but here we are in dev db)
    # ValidationRequest.objects.all().delete()
    # Property.objects.filter(village="Village Test").delete()
