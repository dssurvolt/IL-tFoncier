from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, USSDSession, PasswordResetToken

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('iLôt Foncier Profile', {'fields': ('role', 'phone', 'district', 'village')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('iLôt Foncier Profile', {'fields': ('role', 'full_name', 'district', 'village')}),
    )


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
