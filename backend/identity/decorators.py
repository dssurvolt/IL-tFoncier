from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from identity.models import User

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('web_login')
            
            if request.user.role not in allowed_roles and not request.user.is_superuser:
                messages.error(request, "🛡️ Accès restreint. Vous n'avez pas les permissions nécessaires.")
                return redirect('web_marketplace')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def notary_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web_login')
        
        if request.user.role != User.Role.NOTARY or not hasattr(request.user, 'notary_profile'):
            messages.error(request, "⚖️ Accès réservé aux Notaires Certifiés d'iLôt Foncier.")
            referer = request.META.get('HTTP_REFERER')
            if referer:
                # Éviter une boucle de redirection si le referer est la page elle-même
                if 'notary/dashboard' not in referer:
                    return redirect(referer)
            return redirect('user_dashboard', wallet=str(request.user.id))
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    return role_required([User.Role.ADMIN])(view_func)
