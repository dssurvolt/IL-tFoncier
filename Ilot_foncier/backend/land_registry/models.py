import uuid
from django.db import models # Changed from django.contrib.gis.db
from django.utils.translation import gettext_lazy as _
from identity.models import User

class AuthorizedSurveyor(models.Model):
    """
    Géomètres agréés par l'État.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, unique=True, help_text="Numéro d'agrément officiel")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    organization = models.CharField(max_length=255, null=True, blank=True, help_text="Cabinet ou Administration")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'authorized_surveyors'
        verbose_name = _("Géomètre Agréé")
        verbose_name_plural = _("Géomètres Agréés")

    def __str__(self):
        return f"{self.name} ({self.license_number})"

class Property(models.Model):
    """
    Miroir local des actifs fonciers sur la Blockchain.
    Source de vérité = Smart Contract.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Brouillon / En attente')
        PENDING_SURVEYOR = 'PENDING_SURVEYOR', _('En attente attestation géomètre')
        VALIDATING = 'VALIDATING', _('En cours de validation communautaire')
        ON_CHAIN = 'ON_CHAIN', _('Sécurisé sur Blockchain')
        DISPUTED = 'DISPUTED', _('En litige')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Blockchain Link
    on_chain_id = models.DecimalField(max_digits=78, decimal_places=0, unique=True, null=True, blank=True, help_text="Token ID (uint256) sur le contrat")
    owner_wallet = models.ForeignKey(User, on_delete=models.PROTECT, related_name='properties', to_field='wallet_address', db_column='owner_wallet')
    country = models.CharField(max_length=100, default='Benin', help_text="Pays de la parcelle")
    
    # Geospatial Data (Fallback JSON for No-GDAL env)
    # TODO: Switch back to PointField/PolygonField in Production with PostGIS
    gps_centroid = models.JSONField(help_text="Point central {lat: float, lng: float}")
    gps_boundaries = models.JSONField(help_text="Limites exactes [ {lat, lng}, ... ]")
    
    # Information Foncière
    area_sqm = models.FloatField(null=True, blank=True, help_text="Superficie en m²")
    area_cadastral = models.CharField(max_length=50, null=True, blank=True, help_text="Superficie format cadastral (ex: 01ha 20a 15ca)")
    district = models.CharField(max_length=100, null=True, blank=True, help_text="Nom de l'arrondissement")
    village = models.CharField(max_length=100, null=True, blank=True, help_text="Quartier / Village")
    
    # Validation Technique
    surveyor = models.ForeignKey(AuthorizedSurveyor, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    surveyor_name = models.CharField(max_length=255, null=True, blank=True, help_text="Nom saisi (si hors liste)")
    is_surveyor_validated = models.BooleanField(default=False, help_text="Le géomètre a-t-il certifié les mesures ?")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    @property
    def is_certified(self):
        """Un dossier est certifié si le géomètre a validé ET au moins 2 témoins ont confirmé."""
        witness_count = self.witnesses.filter(is_confirmed=True).count()
        return self.is_surveyor_validated and witness_count >= 2
    last_sync_block = models.BigIntegerField(null=True, blank=True, help_text="Dernier bloc synchronisé")

    class Meta:
        db_table = 'properties'
        verbose_name = _("Propriété")
        verbose_name_plural = _("Propriétés")
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['owner_wallet']),
        ]

    def __str__(self):
        return f"Prop {self.id} ({self.status})"

class PropertyMedia(models.Model):
    """
    Liens vers les documents stockés sur IPFS.
    Aucun fichier binaire n'est stocké en base.
    """
    class MediaType(models.TextChoices):
        PHOTO_LAND = 'PHOTO_LAND', _('Photo du Terrain')
        PHOTO_DOC = 'PHOTO_DOC', _('Photo Document Papier')
        VIDEO_DRONE = 'VIDEO_DRONE', _('Vidéo Drone')
        LEGAL_DOC = 'LEGAL_DOC', _('Document Juridique (PDF/Scan)')
        OTHER_MEDIA = 'OTHER_MEDIA', _('Autre Média')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='media')
    
    file = models.FileField(upload_to="property_media/", null=True, blank=True)
    ipfs_cid = models.CharField(max_length=64, help_text="Content ID IPFS (ex: Qm...)")
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    is_verified = models.BooleanField(default=False, help_text="Hash confirmé sur la blockchain ?")
    
    class Meta:
        db_table = 'property_media'

    def __str__(self):
        return f"{self.media_type} for {self.property_id}"

class BlockchainSyncStatus(models.Model):
    """
    État de santé de l'Indexeur.
    """
    class SyncStatus(models.TextChoices):
        OK = 'OK', _('Synchronisé')
        LAGGING = 'LAGGING', _('En retard')
        STOPPED = 'STOPPED', _('Arrêté / Erreur')

    contract_address = models.CharField(max_length=42, primary_key=True)
    chain_id = models.IntegerField(default=137, help_text="Chain ID (ex: 137 Polygon)")
    last_processed_block = models.BigIntegerField(default=0)
    sync_status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.OK)

    class Meta:
        db_table = 'blockchain_sync_status'

    def __str__(self):
        return f"Sync {self.contract_address}: {self.last_processed_block}"

class PropertyWitness(models.Model):
    """
    Témoins de la transaction foncière.
    """
    class Gender(models.TextChoices):
        MALE = 'M', _('Masculin')
        FEMALE = 'F', _('Féminin')
        OTHER = 'O', _('Autre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='witnesses')
    
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=150)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False, help_text="Le témoin a-t-il validé son implication ?")
    id_card_photo = models.FileField(upload_to="witness_ids/", null=True, blank=True)
    ipfs_cid = models.CharField(max_length=64, null=True, blank=True, help_text="CID de la pièce d'identité")

    class Meta:
        db_table = 'property_witnesses'
        verbose_name = _("Témoin")
        verbose_name_plural = _("Témoins")

    def __str__(self):
        return f"{self.last_name} {self.first_name} (Témoin)"
