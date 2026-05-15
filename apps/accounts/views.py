"""
Account Views - Registration, Login, Logout, Profile, Admin User Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .forms import RegistrationForm, LoginForm, UserUpdateForm, AdminUserForm
from apps.organisations.models import Organisation, SupplierProfile, BuyerProfile, FinancierProfile
from services.permissions import admin_required
from services.audit import create_audit_log
from services.notifications import create_notification

User = get_user_model()

ROLE_MAP = {
    'supplier': 'supplier_admin',
    'buyer': 'buyer_admin',
    'financier': 'financier_admin',
}


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cd = form.cleaned_data
                # Create organisation
                org = Organisation.objects.create(
                    name=cd['organisation_name'],
                    trading_name=cd.get('trading_name') or cd['organisation_name'],
                    organisation_type=cd['account_type'],
                    registration_number=cd['registration_number'],
                    sector=cd['sector'],
                    city=cd['city'],
                    country=cd['country'],
                    contact_email=cd.get('contact_email') or cd['email'],
                    contact_phone=cd.get('contact_phone') or cd['phone'],
                    status='pending',
                )
                # Create profile based on type
                if cd['account_type'] == 'supplier':
                    SupplierProfile.objects.create(organisation=org)
                elif cd['account_type'] == 'buyer':
                    BuyerProfile.objects.create(organisation=org)
                elif cd['account_type'] == 'financier':
                    FinancierProfile.objects.create(organisation=org)

                # Create user
                user = User.objects.create_user(
                    email=cd['email'],
                    password=cd['password'],
                    first_name=cd['first_name'],
                    last_name=cd['last_name'],
                    phone=cd['phone'],
                    role=ROLE_MAP.get(cd['account_type'], 'supplier_user'),
                    organisation=org,
                    is_active=False,
                )
                # Create audit log
                create_audit_log(
                    actor=user, action='registration',
                    entity_type='User', entity_id=str(user.id),
                    new_values={'email': user.email, 'org': org.name},
                    request=request,
                )
                # Notify admins
                for admin_user in User.objects.filter(role__in=['super_admin', 'platform_admin'], is_active=True):
                    create_notification(
                        user=admin_user,
                        title='New Registration',
                        message=f'{user.full_name} from {org.name} has registered as a {cd["account_type"]}.',
                        notification_type='system',
                    )
            return redirect('accounts:pending')
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                if user.organisation and user.organisation.status == 'pending':
                    messages.warning(request, 'Your organisation is still under review.')
                elif user.organisation and user.organisation.status == 'suspended':
                    messages.error(request, 'Your organisation has been suspended. Please contact support.')
                else:
                    messages.warning(request, 'Your account is not yet active. Please wait for admin approval.')
                return render(request, 'auth/login.html', {'form': form})
            login(request, user)
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            create_audit_log(
                actor=user, action='login',
                entity_type='User', entity_id=str(user.id),
                request=request,
            )
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    create_audit_log(
        actor=request.user, action='logout',
        entity_type='User', entity_id=str(request.user.id),
        request=request,
    )
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('public_site:home')


def pending_view(request):
    return render(request, 'auth/pending.html')


def suspended_view(request):
    return render(request, 'auth/suspended.html')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'auth/profile.html', {'form': form})


# --- Admin User Management ---

@login_required
@admin_required
def user_list_view(request):
    users = User.objects.select_related('organisation').all()
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')

    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    if search:
        from django.db.models import Q
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'admin_portal/users/list.html', {
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
@admin_required
def user_detail_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    return render(request, 'admin_portal/users/detail.html', {'user_obj': user_obj})


@login_required
@admin_required
def user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        old_active = user_obj.is_active
        user_obj.is_active = not user_obj.is_active
        user_obj.save(update_fields=['is_active'])
        action = 'user_activated' if user_obj.is_active else 'user_suspended'
        create_audit_log(
            actor=request.user, action=action,
            entity_type='User', entity_id=str(user_obj.id),
            old_values={'is_active': old_active},
            new_values={'is_active': user_obj.is_active},
            request=request,
        )
        create_notification(
            user=user_obj,
            title='Account Status Changed',
            message=f'Your account has been {"activated" if user_obj.is_active else "suspended"}.',
            notification_type='system',
        )
        status_word = 'activated' if user_obj.is_active else 'suspended'
        messages.success(request, f'User {user_obj.full_name} has been {status_word}.')
    return redirect('accounts:user_detail', user_id=user_id)


@login_required
@admin_required
def user_edit_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('accounts:user_detail', user_id=user_id)
    else:
        form = AdminUserForm(instance=user_obj)
    return render(request, 'admin_portal/users/edit.html', {'form': form, 'user_obj': user_obj})
