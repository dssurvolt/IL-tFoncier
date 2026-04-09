from django.contrib import admin
from .models import AuthorizedSurveyor, Property, PropertyMedia, PropertyWitness

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

@admin.register(PropertyMedia)
class PropertyMediaAdmin(admin.ModelAdmin):
    list_display = ('property', 'media_type')
    list_filter = ('media_type',)
    search_fields = ('property__id',)


@admin.register(PropertyWitness)
class PropertyWitnessAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'property', 'is_confirmed')
    list_filter = ('is_confirmed', 'gender')
    search_fields = ('last_name', 'first_name', 'phone', 'email')
