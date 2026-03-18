from identity.models import User

def notary_context(request):
    """
    Fournit des informations globales sur le statut de notaire dans tous les templates.
    """
    is_notary = False
    notary_profile = None

    if request.user.is_authenticated:
        # Vérification stricte du rôle
        has_role = (getattr(request.user, 'role', None) == 'NOTARY')
        has_profile = False
        try:
            notary_profile = getattr(request.user, 'notary_profile', None)
            has_profile = notary_profile is not None
        except:
            has_profile = False

        is_notary = has_role and has_profile
        
        # Log discret pour le debug interne
        import logging
        logger = logging.getLogger(__name__)
        if is_notary:
            logger.debug(f"TEMPLATING: User {request.user.email} seen as NOTARY")

    return {
        'is_notary': is_notary,
        'notary_profile': notary_profile if is_notary else None
    }
