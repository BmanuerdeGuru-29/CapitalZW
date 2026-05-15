"""Dashboard Views - Role-based dashboards with KPI cards."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.invoices.models import Invoice
from apps.offers.models import FinancingOffer
from apps.settlements.models import Settlement, Repayment
from apps.organisations.models import Organisation
from apps.documents.models import KYCDocument
from apps.audit.models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def index(request):
    """Redirect to the correct dashboard based on role."""
    user = request.user
    if not user.is_active:
        return redirect('accounts:pending')
    if user.organisation and user.organisation.status == 'pending':
        return redirect('accounts:pending')
    return redirect(user.dashboard_url)


@login_required
def supplier_dashboard(request):
    org = request.user.organisation
    if not org:
        return render(request, 'supplier/dashboard.html', {'no_org': True})

    invoices = Invoice.objects.filter(supplier=org)
    total_invoices = invoices.count()
    approved_value = invoices.filter(
        status__in=['available_for_financing', 'offer_received', 'offer_accepted', 'settlement_pending', 'settled', 'repaid']
    ).aggregate(total=Sum('invoice_amount'))['total'] or 0
    offers_count = FinancingOffer.objects.filter(invoice__supplier=org, status='submitted').count()
    funded = invoices.filter(status__in=['settled', 'repaid']).aggregate(total=Sum('invoice_amount'))['total'] or 0
    pending_settlements = invoices.filter(status='settlement_pending').count()

    recent_invoices = invoices[:5]
    pending_offers = FinancingOffer.objects.filter(
        invoice__supplier=org, status='submitted'
    ).select_related('invoice', 'financier')[:5]

    return render(request, 'supplier/dashboard.html', {
        'total_invoices': total_invoices,
        'approved_value': approved_value,
        'offers_count': offers_count,
        'funded': funded,
        'pending_settlements': pending_settlements,
        'recent_invoices': recent_invoices,
        'pending_offers': pending_offers,
    })


@login_required
def buyer_dashboard(request):
    org = request.user.organisation
    if not org:
        return render(request, 'buyer/dashboard.html', {'no_org': True})

    invoices = Invoice.objects.filter(buyer=org)
    pending_approvals = invoices.filter(status='pending_buyer_approval').count()
    approved_value = invoices.filter(
        status__in=['available_for_financing', 'offer_received', 'offer_accepted', 'settlement_pending', 'settled']
    ).aggregate(total=Sum('invoice_amount'))['total'] or 0
    rejected = invoices.filter(status='rejected').count()
    pending_queue = invoices.filter(status='pending_buyer_approval')[:10]
    recent_approved = invoices.filter(status__in=['available_for_financing', 'offer_received', 'settled'])[:5]

    return render(request, 'buyer/dashboard.html', {
        'pending_approvals': pending_approvals,
        'approved_value': approved_value,
        'rejected': rejected,
        'pending_queue': pending_queue,
        'recent_approved': recent_approved,
    })


@login_required
def financier_dashboard(request):
    org = request.user.organisation
    if not org:
        return render(request, 'financier/dashboard.html', {'no_org': True})

    available = Invoice.objects.filter(
        status__in=['available_for_financing', 'offer_received']
    ).aggregate(total=Sum('invoice_amount'))['total'] or 0
    my_offers = FinancingOffer.objects.filter(financier=org)
    submitted = my_offers.filter(status='submitted').count()
    accepted = my_offers.filter(status='accepted').count()
    portfolio = my_offers.filter(status__in=['accepted', 'settled']).aggregate(
        total=Sum('offered_amount'))['total'] or 0
    marketplace_invoices = Invoice.objects.filter(
        status__in=['available_for_financing', 'offer_received']
    ).select_related('supplier', 'buyer')[:5]
    recent_offers = my_offers.select_related('invoice')[:5]

    return render(request, 'financier/dashboard.html', {
        'available_value': available,
        'submitted': submitted,
        'accepted': accepted,
        'portfolio': portfolio,
        'marketplace_invoices': marketplace_invoices,
        'recent_offers': recent_offers,
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('dashboard:index')

    total_users = User.objects.count()
    total_orgs = Organisation.objects.count()
    total_invoice_value = Invoice.objects.aggregate(total=Sum('invoice_amount'))['total'] or 0
    total_financed = FinancingOffer.objects.filter(
        status__in=['accepted', 'settled']
    ).aggregate(total=Sum('offered_amount'))['total'] or 0
    pending_kyc = KYCDocument.objects.filter(status='pending').count()
    pending_approvals = Invoice.objects.filter(status='pending_buyer_approval').count()
    pending_orgs = Organisation.objects.filter(status='pending').count()

    recent_registrations = Organisation.objects.filter(status='pending').order_by('-created_at')[:5]
    high_value_invoices = Invoice.objects.order_by('-invoice_amount')[:5]
    recent_settlements = Settlement.objects.select_related('invoice').order_by('-created_at')[:5]

    return render(request, 'admin_portal/dashboard.html', {
        'total_users': total_users,
        'total_orgs': total_orgs,
        'total_invoice_value': total_invoice_value,
        'total_financed': total_financed,
        'pending_kyc': pending_kyc,
        'pending_approvals': pending_approvals,
        'pending_orgs': pending_orgs,
        'recent_registrations': recent_registrations,
        'high_value_invoices': high_value_invoices,
        'recent_settlements': recent_settlements,
    })


@login_required
def compliance_dashboard(request):
    if not request.user.is_compliance:
        return redirect('dashboard:index')
    pending_kyc = KYCDocument.objects.filter(status='pending').select_related('organisation')
    return render(request, 'compliance/dashboard.html', {'pending_kyc': pending_kyc})


@login_required
def auditor_dashboard(request):
    if not request.user.is_auditor:
        return redirect('dashboard:index')
    recent_logs = AuditLog.objects.select_related('actor')[:20]
    return render(request, 'auditor/dashboard.html', {'recent_logs': recent_logs})
