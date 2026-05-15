"""
Permission Decorators and Helpers
"""
from functools import wraps
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """Decorator that checks if user has one of the allowed roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard:index')
            if request.user.organisation and request.user.organisation.is_suspended:
                messages.error(request, 'Your organisation has been suspended.')
                return redirect('accounts:suspended')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def supplier_required(view_func):
    return role_required(settings.SUPPLIER_ROLES)(view_func)


def buyer_required(view_func):
    return role_required(settings.BUYER_ROLES)(view_func)


def financier_required(view_func):
    return role_required(settings.FINANCIER_ROLES)(view_func)


def admin_required(view_func):
    return role_required(settings.ADMIN_ROLES)(view_func)


def compliance_required(view_func):
    return role_required(settings.COMPLIANCE_ROLES)(view_func)


def auditor_required(view_func):
    return role_required(settings.AUDITOR_ROLES)(view_func)


def admin_or_auditor_required(view_func):
    return role_required(settings.ADMIN_ROLES + settings.AUDITOR_ROLES)(view_func)


def admin_or_compliance_required(view_func):
    return role_required(settings.ADMIN_ROLES + settings.COMPLIANCE_ROLES)(view_func)


def organisation_approved_required(view_func):
    """Ensure user's organisation is approved before access."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        org = request.user.organisation
        if org and not org.is_approved:
            messages.warning(request, 'Your organisation must be approved before you can access this feature.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return _wrapped


def can_user_access_invoice(user, invoice):
    """Check if user can access an invoice based on role and organisation."""
    if user.is_admin or user.is_compliance or user.is_auditor:
        return True
    if user.is_supplier and user.organisation == invoice.supplier:
        return True
    if user.is_buyer and user.organisation == invoice.buyer:
        return True
    if user.is_financier:
        # Financiers can see available invoices or ones they have offers on
        if invoice.status in ['available_for_financing', 'offer_received']:
            return True
        if invoice.offers.filter(financier=user.organisation).exists():
            return True
    return False


def can_user_access_offer(user, offer):
    """Check if user can access an offer."""
    if user.is_admin or user.is_compliance or user.is_auditor:
        return True
    if user.is_supplier and user.organisation == offer.invoice.supplier:
        return True
    if user.is_financier and user.organisation == offer.financier:
        return True
    return False
