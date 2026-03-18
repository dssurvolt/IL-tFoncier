from django.contrib import admin
from .models import AuthorizedSurveyor, Property, PropertyMedia, BlockchainSyncStatus, PropertyWitness

@admin.register(AuthorizedSurveyor)
class AuthorizedSurveyorAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'license_number', 'email')

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner_wallet', 'district', 'village', 'status', 'is_certified')
    list_filter = ('status', 'country', 'district')
    search_fields = ('id', 'owner_wallet__email', 'owner_wallet__wallet_address', 'district', 'village')
    readonly_fields = ('on_chain_id', 'last_sync_block')

@admin.register(PropertyMedia)
class PropertyMediaAdmin(admin.ModelAdmin):
    list_display = ('property', 'media_type', 'ipfs_cid', 'is_verified')
    list_filter = ('media_type', 'is_verified')
    search_fields = ('property__id', 'ipfs_cid')

@admin.register(BlockchainSyncStatus)
class BlockchainSyncStatusAdmin(admin.ModelAdmin):
    list_display = ('contract_address', 'chain_id', 'last_processed_block', 'sync_status')
    list_filter = ('sync_status', 'chain_id')

@admin.register(PropertyWitness)
class PropertyWitnessAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'property', 'is_confirmed')
    list_filter = ('is_confirmed', 'gender')
    search_fields = ('last_name', 'first_name', 'phone', 'email')
