"""Notification views."""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()[:50]
    return render(request, 'components/notifications.html', {'notifications': notifications})


@login_required
def mark_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.is_read = True
    notif.read_at = timezone.now()
    notif.save(update_fields=['is_read', 'read_at'])
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect('notifications:list')
