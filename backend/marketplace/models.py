import uuid
import builtins
from django.db import models
from django.utils.translation import gettext_lazy as _
from land_registry.models import Property
from identity.models import User

from django.utils import timezone

class Listing(models.Model):
    """
    Offre de vente (Layer 2).
    """
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('En vente')
        SOLD = 'SOLD', _('Vendu')
        CANCELLED = 'CANCELLED', _('Annulé')

    class ListingType(models.TextChoices):
        SALE = 'SALE', _('À vendre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='listings')
    
    listing_type = models.CharField(max_length=10, choices=ListingType.choices, default=ListingType.SALE)
    price_fiat = models.DecimalField(max_digits=15, decimal_places=2, help_text="Prix affiché en FCFA")
    is_negotiable = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'listings'

    @builtins.property
    def is_under_contract(self):
        """Vérifie si une transaction notariale est active sur cette propriété."""
        from notaries.models import TransactionFolio
        return TransactionFolio.objects.filter(
            property=self.property,
            status__in=[
                'STEP1_NOTARY_SELECTED',
                'STEP2_ID_VERIFIED',
                'STEP3_DEED_SIGNED',
                'STEP4_ANDF_DEPOSITED',
                'STEP5_TITLE_MODIFIED'
            ]
        ).exists()

    def __str__(self):
        return f"Annonce {self.property.village or 'Parcelle'} - {self.price_fiat} FCFA"

class Notification(models.Model):
    """
    Système d'alerte utilisateur.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    
    type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'read_at']),
        ]

    def __str__(self):
        return f"Notif for {self.user}: {self.type}"

class MarketplaceInquiry(models.Model):
    """
    Suit les demandes d'informations (PMF Metric Tracking).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='inquiries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketplace_inquiries'
        verbose_name = "Demande d'information"

    def __str__(self):
        return f"Inquiry by {self.user.email} on {self.listing.id}"

class MarketplaceView(models.Model):
    """
    Suit les consultations de la marketplace (Traçabilité accrue).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='views', null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    view_type = models.CharField(max_length=50, default='MARKETPLACE_HOME') # MARKETPLACE_HOME | PROPERTY_DETAIL
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketplace_views'
        verbose_name = "Consultation Marketplace"

    def __str__(self):
        user_name = self.user.email if self.user else "Anonymous"
        return f"{self.view_type} by {user_name} at {self.created_at}"

class ChatRoom(models.Model):
    """
    Espace de discussion privé entre un acheteur et un vendeur.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='chat_rooms')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_rooms'
        unique_together = ('listing', 'buyer', 'seller')

    def __str__(self):
        return f"Chat: {self.buyer.full_name} / {self.seller.full_name} - {self.listing.property.village or 'Parcelle'}"

class ChatMessage(models.Model):
    """
    Message individuel dans un ChatRoom.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender.full_name} at {self.created_at}"
