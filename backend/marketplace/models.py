import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from land_registry.models import Property
from identity.models import User

class Listing(models.Model):
    """
    Offre de vente (Layer 2).
    """
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('En vente')
        SOLD = 'SOLD', _('Vendu')
        CANCELLED = 'CANCELLED', _('Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='listings')
    
    price_fiat = models.DecimalField(max_digits=15, decimal_places=2, help_text="Prix affiché en FCFA")
    price_crypto = models.DecimalField(max_digits=18, decimal_places=6, help_text="Équivalent stablecoin (cUSD)")
    
    escrow_contract = models.CharField(max_length=42, blank=True, help_text="Adresse du contrat séquestre déployé")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    
    class Meta:
        db_table = 'listings'

    def __str__(self):
        return f"Listing {self.id} for {self.property_id}"

class TransactionsHistory(models.Model):
    """
    Journal d'activité enrichi (Off-chain + On-chain).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tx_hash = models.CharField(max_length=66, unique=True, help_text="Hash de la transaction blockchain")
    
    event_type = models.CharField(max_length=50, db_index=True, help_text="MINT, TRANSFER, VALIDATE, DISPUTE")
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42, null=True, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'transactions_history'
        verbose_name_plural = "Transactions History"

    def __str__(self):
        return f"{self.event_type} - {self.tx_hash}"

class Notification(models.Model):
    """
    Système d'alerte utilisateur.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_wallet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', to_field='wallet_address', db_column='user_wallet')
    
    type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user_wallet', 'read_at']),
        ]

    def __str__(self):
        return f"Notif for {self.user_id}: {self.type}"
