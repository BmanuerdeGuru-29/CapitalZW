"""Audit log views for admin and auditor."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AuditLog
from services.permissions import admin_or_auditor_required


@login_required
@admin_or_auditor_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('actor', 'organisation').all()
    action_filter = request.GET.get('action', '')
    entity_filter = request.GET.get('entity', '')
    search = request.GET.get('q', '')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if entity_filter:
        logs = logs.filter(entity_type=entity_filter)
    if search:
        from django.db.models import Q
        logs = logs.filter(
            Q(action__icontains=search) |
            Q(entity_type__icontains=search) |
            Q(actor__email__icontains=search)
        )

    logs = logs[:200]
    actions = AuditLog.objects.values_list('action', flat=True).distinct()[:50]
    entities = AuditLog.objects.values_list('entity_type', flat=True).distinct()[:20]

    return render(request, 'admin_portal/audit/list.html', {
        'logs': logs,
        'action_filter': action_filter,
        'entity_filter': entity_filter,
        'search': search,
        'actions': actions,
        'entities': entities,
    })
