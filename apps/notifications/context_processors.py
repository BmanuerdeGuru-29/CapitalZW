"""Context processor for notifications in navbar."""


def unread_notifications(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        recent = request.user.notifications.filter(is_read=False)[:5]
        return {'unread_notification_count': count, 'recent_notifications': recent}
    return {'unread_notification_count': 0, 'recent_notifications': []}
