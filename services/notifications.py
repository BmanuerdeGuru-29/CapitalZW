"""
Notification Service - Create notifications for workflow events.
"""
from apps.notifications.models import Notification


from apps.notifications.tasks import send_email_notification_task

def create_notification(user, title, message, notification_type='system', related_entity=None):
    """Create an in-app notification for a user and queue an email."""
    entity_type = ''
    entity_id = ''
    if related_entity:
        entity_type = related_entity.__class__.__name__
        entity_id = str(related_entity.pk)

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        channel='in_app',
        related_entity_type=entity_type,
        related_entity_id=entity_id,
    )
    
    # Trigger async email
    send_email_notification_task.delay(user.email, title, message)
    
    return notification


def notify_org_users(organisation, title, message, notification_type='system', related_entity=None, exclude_user=None):
    """Send notification to all active users in an organisation."""
    users = organisation.users.filter(is_active=True)
    if exclude_user:
        users = users.exclude(id=exclude_user.id)
    for user in users:
        create_notification(user, title, message, notification_type, related_entity)
