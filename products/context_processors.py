from .models import Notification


def notification_context(request):
    """
    Makes notification information available
    to all templates.
    """

    if not request.user.is_authenticated:
        return {
            "unread_notifications": 0,
            "recent_notifications": [],
        }

    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    recent_notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")[:5]
    )

    return {
        "unread_notifications": unread_notifications,
        "recent_notifications": recent_notifications,
    }