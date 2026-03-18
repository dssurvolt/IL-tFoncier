from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuthNonce, USSDSession, PasswordResetToken

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_staff', 'reputation_score')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'full_name', 'wallet_address')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('iLôt Foncier Profile', {'fields': ('role', 'wallet_address', 'phone_hash', 'encrypted_phone', 'reputation_score', 'district', 'village')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('iLôt Foncier Profile', {'fields': ('role', 'full_name', 'wallet_address', 'district', 'village')}),
    )

@admin.register(AuthNonce)
class AuthNonceAdmin(admin.ModelAdmin):
    list_display = ('wallet_address', 'nonce', 'expires_at')
    search_fields = ('wallet_address',)

@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'phone_number', 'current_menu', 'updated_at')
    list_filter = ('current_menu',)
    search_fields = ('phone_number', 'session_id')

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used')
    list_filter = ('used',)
    search_fields = ('user__email', 'token')
