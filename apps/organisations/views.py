"""Organisation views - Admin management of organisations."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Organisation
from services.permissions import admin_required, compliance_required
from services.audit import create_audit_log
from services.notifications import create_notification


@login_required
@admin_required
def org_list_view(request):
    orgs = Organisation.objects.all()
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')

    if type_filter:
        orgs = orgs.filter(organisation_type=type_filter)
    if status_filter:
        orgs = orgs.filter(status=status_filter)
    if search:
        from django.db.models import Q
        orgs = orgs.filter(Q(name__icontains=search) | Q(trading_name__icontains=search))

    return render(request, 'admin_portal/organisations/list.html', {
        'organisations': orgs,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
@admin_required
def org_detail_view(request, org_id):
    org = get_object_or_404(Organisation, id=org_id)
    users = org.users.all()
    return render(request, 'admin_portal/organisations/detail.html', {'org': org, 'users': users})


@login_required
@admin_required
def org_approve_view(request, org_id):
    org = get_object_or_404(Organisation, id=org_id)
    if request.method == 'POST':
        old_status = org.status
        org.status = 'approved'
        org.save(update_fields=['status'])
        # Activate org users
        org.users.update(is_active=True)
        create_audit_log(
            actor=request.user, action='organisation_approved',
            entity_type='Organisation', entity_id=str(org.id),
            old_values={'status': old_status}, new_values={'status': 'approved'},
            request=request,
        )
        for u in org.users.all():
            create_notification(
                user=u, title='Organisation Approved',
                message=f'Your organisation {org.name} has been approved. You can now access the platform.',
                notification_type='system',
            )
        messages.success(request, f'{org.name} has been approved.')
    return redirect('organisations:detail', org_id=org_id)


@login_required
@admin_required
def org_reject_view(request, org_id):
    org = get_object_or_404(Organisation, id=org_id)
    if request.method == 'POST':
        old_status = org.status
        org.status = 'rejected'
        org.save(update_fields=['status'])
        create_audit_log(
            actor=request.user, action='organisation_rejected',
            entity_type='Organisation', entity_id=str(org.id),
            old_values={'status': old_status}, new_values={'status': 'rejected'},
            request=request,
        )
        for u in org.users.all():
            create_notification(
                user=u, title='Organisation Rejected',
                message=f'Your organisation {org.name} registration has been rejected.',
                notification_type='system',
            )
        messages.warning(request, f'{org.name} has been rejected.')
    return redirect('organisations:detail', org_id=org_id)


@login_required
@admin_required
def org_suspend_view(request, org_id):
    org = get_object_or_404(Organisation, id=org_id)
    if request.method == 'POST':
        old_status = org.status
        org.status = 'suspended'
        org.save(update_fields=['status'])
        create_audit_log(
            actor=request.user, action='organisation_suspended',
            entity_type='Organisation', entity_id=str(org.id),
            old_values={'status': old_status}, new_values={'status': 'suspended'},
            request=request,
        )
        messages.warning(request, f'{org.name} has been suspended.')
    return redirect('organisations:detail', org_id=org_id)
