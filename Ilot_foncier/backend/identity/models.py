import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserManager(BaseUserManager):
    """Manager pour gérer la création d'utilisateurs via Email."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Utilisateur Hybride (Web3 + Mobile).
    Utilise l'email comme identifiant principal.
    """
    class Role(models.TextChoices):
        USER = 'USER', _('Utilisateur Standard')
        WITNESS = 'WITNESS', _('Témoin Certifié')
        CHIEF = 'CHIEF', _('Chef de Localité')
        ADMIN = 'ADMIN', _('Administrateur')

    username = None  # On désactive le username par défaut
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, help_text="Email de connexion")
    wallet_address = models.CharField(max_length=42, unique=True, null=True, blank=True, help_text="Adresse publique Ethereum/Polygon (0x...) - Optionnel")
    
    # Privacy & Security
    phone_hash = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text="SHA-256 du numéro de téléphone")
    encrypted_phone = models.CharField(max_length=255, null=True, blank=True, help_text="Numéro chiffré pour notifications")
    
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER, db_index=True)
    full_name = models.CharField(max_length=255, null=True, blank=True, help_text="Nom et Prénom (pas de chiffres)")
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, default='Benin', help_text="Pays de résidence")
    district = models.CharField(max_length=100, null=True, blank=True, help_text="Arrondissement / Commune")
    village = models.CharField(max_length=100, null=True, blank=True, help_text="Quartier / Village")
    reputation_score = models.IntegerField(default=50, help_text="Score 0-100 basé sur la fiabilité")
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        name = self.full_name if self.full_name else self.email
        return f"{name} ({self.role})"

    class Meta:
        db_table = 'users'
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        indexes = [
            models.Index(fields=['phone_hash']),
            models.Index(fields=['role']),
            models.Index(fields=['wallet_address']),
        ]

class AuthNonce(models.Model):
    """
    Sécurité pour le 'Sign-in with Ethereum'.
    Empêche les attaques par rejeu.
    """
    wallet_address = models.CharField(max_length=42, primary_key=True)
    nonce = models.CharField(max_length=32, help_text="Chaîne aléatoire à signer")
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'auth_nonces'

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Nonce for {self.wallet_address}"

class USSDSession(models.Model):
    """
    Gestion d'état pour le protocole USSD (Stateless).
    Optimisé pour la rapidité (< 200ms).
    """
    session_id = models.CharField(max_length=64, primary_key=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    current_menu = models.CharField(max_length=50, default='HOME')
    input_buffer = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        # TTL de 3 minutes (180 secondes)
        return (timezone.now() - self.updated_at).total_seconds() > 180

    class Meta:
        db_table = 'ussd_sessions'
        verbose_name = _("Session USSD")
        indexes = [
            models.Index(fields=['phone_number']),
        ]

class PasswordResetToken(models.Model):
    """
    Token de réinitialisation de mot de passe.
    Valide pendant 1 heure.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = _("Token de Réinitialisation")
        verbose_name_plural = _("Tokens de Réinitialisation")
    
    def is_valid(self):
        """Vérifie si le token est toujours valide"""
        return not self.used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Marque le token comme utilisé"""
        self.used = True
        self.save()
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
