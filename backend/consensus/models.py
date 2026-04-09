import uuid
from django.db import models # Changed from django.contrib.gis.db
from django.utils.translation import gettext_lazy as _
from identity.models import User
from land_registry.models import Property

class ValidationRequest(models.Model):
    """
    Processus de validation communautaire.
    """
    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Ouvert aux votes')
        COMPLETED = 'COMPLETED', _('Validé (Consensus atteint)')
        REJECTED = 'REJECTED', _('Rejeté (Fraude détectée)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='validation_requests')
    requester_email = models.CharField(max_length=150, help_text="Email du demandeur")
    
    # Proof of Presence (Fallback JSON)
    gps_at_request = models.JSONField(help_text="Localisation {lat, lng}")
    
    min_witnesses = models.IntegerField(default=3, help_text="Nombre minimum de témoins requis")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)

    class Meta:
        db_table = 'validation_requests'

    def __str__(self):
        return f"Req {self.id} ({self.status})"

class WitnessVote(models.Model):
    """
    Vote individuel d'un témoin (Voisin/Chef).
    Identifié par son identité légale complète pour responsabilité juridique.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(ValidationRequest, on_delete=models.CASCADE, related_name='votes')
    
    # Identité Légale Universelle (Responsabilité Juridique Globale)
    witness_full_name = models.CharField(max_length=255, help_text="Nom et Prénoms complets")
    witness_birth_date = models.DateField(null=True, blank=True, help_text="Date de naissance (YYYY-MM-DD)")
    witness_id_number = models.CharField(max_length=100, help_text="Numéro de Passeport ou Carte d'Identité Nationale")
    witness_phone = models.CharField(max_length=20, help_text="Numéro de téléphone")
    
    # Optionnel: User si disponible
    witness_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='witness_votes')
    
    # Proof of Presence (CRITIQUE)
    witness_gps = models.JSONField(help_text="Localisation {lat, lng}")
    
    vote_result = models.BooleanField(help_text="True=Valide, False=Fraude")

    class Meta:
        db_table = 'witness_votes'
        unique_together = ('request', 'witness_id_number') # Un vote par document d'identité par demande

    def __str__(self):
        return f"Vote by {self.witness_full_name} ({self.witness_id_number}) on {self.request_id}"

class GeoFence(models.Model):
    """
    Découpage administratif pour assigner les validateurs locaux (Chefs).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    boundary = models.JSONField(help_text="Polygone GeoJSON")
    chief_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Chef de zone responsable")

    class Meta:
        db_table = 'geo_fences'
    
    def __str__(self):
        return self.name
