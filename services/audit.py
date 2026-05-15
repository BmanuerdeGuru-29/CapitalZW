"""
Audit Service - Create audit log entries.
"""
from apps.audit.models import AuditLog


def get_client_ip(request):
    if request is None:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def create_audit_log(actor, action, entity_type, entity_id='', old_values=None, new_values=None, request=None):
    """Create an append-only audit log entry."""
    ip = get_client_ip(request) if request else None
    ua = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    org = getattr(actor, 'organisation', None)
    role = getattr(actor, 'role', '')

    return AuditLog.objects.create(
        actor=actor if actor and hasattr(actor, 'pk') and actor.pk else None,
        actor_role=role,
        organisation=org,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_values=old_values,
        new_values=new_values,
        ip_address=ip,
        user_agent=ua,
    )
