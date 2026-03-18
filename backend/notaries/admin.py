from django.contrib import admin
from .models import Notary, TransactionFolio

@admin.register(Notary)
class NotaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'office_name', 'city', 'is_verified', 'avg_processing_time_days')
    list_filter = ('city', 'is_verified')
    search_fields = ('name', 'office_name', 'license_number')

@admin.register(TransactionFolio)
class TransactionFolioAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'buyer', 'seller', 'notary', 'status')
    list_filter = ('status', 'notary')
    search_fields = ('andf_dossier_number', 'buyer__email', 'seller__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Acteurs', {
            'fields': ('property', 'buyer', 'seller', 'notary')
        }),
        ('Avancement', {
            'fields': ('status', 'andf_dossier_number')
        }),
        ('Historique', {
            'fields': ('step2_verified_at', 'step3_signed_at', 'step4_deposited_at', 'step5_modified_at', 'step6_completed_at', 'created_at', 'updated_at')
        }),
    )
