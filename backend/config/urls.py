from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.conf import settings
from django.conf.urls.static import static
from land_registry.views import (
    dashboard, web_properties, PropertyListAPI, PropertyDetailAPI, 
    user_dashboard, web_register_user, web_login, web_logout, web_property_detail, 
    web_profile, web_password_reset, web_add_property
)
from consensus.views import web_validation, ValidationRequestAPI
from identity.ussd_views import web_ussd, USSDGateway
from identity.api_views import UserProfileAPI
from identity.views import AuthAPI
from identity.password_reset_views import PasswordResetAPI
from marketplace.views import ListingListAPI, web_marketplace, web_create_listing
from config.swagger_views import swagger_ui

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('web_login'), name='login_home'),
    # Espace Citoyen (Public & Personnel)
    path('login/', web_login, name='web_login'),
    path('logout/', web_logout, name='web_logout'),
    path('password-reset/', web_password_reset, name='web_password_reset'),
    path('password-reset/confirm/', lambda r: render(r, 'password_reset_confirm.html'), name='web_password_reset_confirm'),
    path('register/', web_register_user, name='web_register'),
    path('add-property/<str:wallet>/', web_add_property, name='web_add_property'),
    path('marketplace/', web_marketplace, name='web_marketplace'),
    path('marketplace/create/<uuid:property_id>/', web_create_listing, name='web_create_listing'),
    path('dashboard/<str:wallet>/', user_dashboard, name='user_dashboard'),
    path('profile/<str:wallet>/', web_profile, name='web_profile'),
    path('property/<uuid:pk>/', web_property_detail, name='web_property_detail'),
    
    # Espace Supervision (Admin)
    path('supervision/', dashboard, name='dashboard'),
    path('supervision/properties/', web_properties, name='web_properties'),
    path('supervision/validation/', web_validation, name='web_validation'),
    path('supervision/ussd/', web_ussd, name='web_ussd'),
    
    # API Routes (REST)
    path('api/properties/', PropertyListAPI.as_view(), name='api_property_list'),
    path('api/properties/<uuid:pk>/', PropertyDetailAPI.as_view(), name='api_property_detail'),
    path('api/marketplace/listings/', ListingListAPI.as_view(), name='api_marketplace_list'),
    path('api/identity/profile/<str:wallet>/', UserProfileAPI.as_view(), name='api_user_profile'),
    
    # Consensus Flow
    path('api/validation/<str:action>/', ValidationRequestAPI.as_view(), name='api_validation_flow'),
    
    # Authentication API
    path('api/auth/<str:action>/', AuthAPI.as_view(), name='api_auth'),
    path('api/password-reset/<str:action>/', PasswordResetAPI.as_view(), name='api_password_reset'),
    
    # USSD Gateway
    path('ussd/', USSDGateway.as_view(), name='ussd_gateway'),
    
    # Documentation
    path('swagger/', swagger_ui, name='swagger_ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
