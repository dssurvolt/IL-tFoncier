from marketplace.models import Notification

def notification_count(request):
    """
    Rend disponible le nombre de notifications non lues dans tous les templates.
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(user_wallet=request.user, read_at__isnull=True).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
