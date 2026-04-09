from django.contrib import admin
from .models import Listing, Notification, MarketplaceInquiry, MarketplaceView

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'price_fiat', 'status')
    list_filter = ('status',)
    search_fields = ('property__id',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'read_at')
    list_filter = ('type', 'read_at')
    search_fields = ('user__email',)

@admin.register(MarketplaceInquiry)
class MarketplaceInquiryAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'listing__id')

@admin.register(MarketplaceView)
class MarketplaceViewAdmin(admin.ModelAdmin):
    list_display = ('view_type', 'user', 'property', 'created_at', 'ip_address')
    list_filter = ('view_type', 'created_at')
    search_fields = ('user__email', 'ip_address')
