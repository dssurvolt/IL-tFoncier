import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from identity.models import User
from land_registry.models import Property

class Notary(models.Model):
    """
    Notaires certifiés partenaires de la plateforme.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Nom complet du Notaire")
    office_name = models.CharField(max_length=255, help_text="Nom de l'étude / cabinet")
    license_number = models.CharField(max_length=100, unique=True, help_text="Numéro de licence officielle")
    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notary_profile')
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(help_text="Adresse physique de l'étude")
    city = models.CharField(max_length=100, default="Cotonou")
    
    gps_location = models.JSONField(null=True, blank=True, help_text="Localisation {lat: float, lng: float}")
    
    avg_processing_time_days = models.IntegerField(default=30, help_text="Temps moyen de traitement constaté")
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié par iLôt")
    
    pricing_guide = models.JSONField(null=True, blank=True, help_text="Grille tarifaire standardisée")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notaries'
        verbose_name = _("Notaire")
        verbose_name_plural = _("Notaires")

    def __str__(self):
        return f"Me {self.name} ({self.office_name})"

class TransactionFolio(models.Model):
    """
    Chaîne de valeur sécurisée d'une transaction foncière (Étapes 1 à 6).
    """
    class Step(models.TextChoices):
        STEP1_NOTARY_SELECTED = 'STEP1_NOTARY_SELECTED', _('1. Notaire Choisi')
        STEP2_ID_VERIFIED = 'STEP2_ID_VERIFIED', _('2. Identités Vérifiées (Présence)')
        STEP3_DEED_SIGNED = 'STEP3_DEED_SIGNED', _('3. Acte de Vente Signé')
        STEP4_ANDF_DEPOSITED = 'STEP4_ANDF_DEPOSITED', _('4. Déposé à l\'ANDF')
        STEP5_TITLE_MODIFIED = 'STEP5_TITLE_MODIFIED', _('5. Titre Modifié par l\'ANDF')
        STEP6_COMPLETED = 'STEP6_COMPLETED', _('6. Titre Récupéré / Terminé')
        CANCELLED = 'CANCELLED', _('Annulée')

    STEP_ORDER = {
        Step.STEP1_NOTARY_SELECTED: 1,
        Step.STEP2_ID_VERIFIED: 2,
        Step.STEP3_DEED_SIGNED: 3,
        Step.STEP4_ANDF_DEPOSITED: 4,
        Step.STEP5_TITLE_MODIFIED: 5,
        Step.STEP6_COMPLETED: 6,
        Step.CANCELLED: 0,
    }

    @property
    def status_order(self):
        return self.STEP_ORDER.get(self.status, 0)

    @property
    def progress_percentage(self):
        order = self.status_order
        if order == 0: return 0
        return int((order / 6) * 100)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='transactions')
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales')
    notary = models.ForeignKey(Notary, on_delete=models.CASCADE, related_name='transactions')
    
    status = models.CharField(max_length=30, choices=Step.choices, default=Step.STEP1_NOTARY_SELECTED, db_index=True)
    
    # Suivi ANDF
    andf_dossier_number = models.CharField(max_length=100, null=True, blank=True, help_text="Numéro de dépôt officiel ANDF")
    
    # Timestamps par étape
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historique précis (nullable au début)
    step2_verified_at = models.DateTimeField(null=True, blank=True)
    step3_signed_at = models.DateTimeField(null=True, blank=True)
    step4_deposited_at = models.DateTimeField(null=True, blank=True)
    step5_modified_at = models.DateTimeField(null=True, blank=True)
    step6_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transaction_folios'
        verbose_name = _("Folio de Transaction")
        verbose_name_plural = _("Folios de Transaction")

    def __str__(self):
        return f"Dossier {self.property.village or 'Parcelle'} - Acheteur: {self.buyer.full_name or self.buyer.email} ({self.get_status_display()})"
