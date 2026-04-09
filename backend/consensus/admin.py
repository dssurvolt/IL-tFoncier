from django.contrib import admin
from .models import ValidationRequest, WitnessVote, GeoFence

@admin.register(ValidationRequest)
class ValidationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'requester_email', 'min_witnesses', 'status')
    list_filter = ('status',)
    search_fields = ('requester_email', 'property__id')

@admin.register(WitnessVote)
class WitnessVoteAdmin(admin.ModelAdmin):
    list_display = ('witness_full_name', 'witness_id_number', 'request', 'vote_result')
    list_filter = ('vote_result',)
    search_fields = ('witness_full_name', 'witness_id_number', 'witness_phone', 'request__id')

@admin.register(GeoFence)
class GeoFenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'chief_user')
    search_fields = ('name', 'chief_user__email')
