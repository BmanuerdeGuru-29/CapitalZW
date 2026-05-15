"""Reports Views - Filtered reports with CSV export."""
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.invoices.models import Invoice
from apps.offers.models import FinancingOffer
from apps.settlements.models import Settlement
from apps.audit.models import AuditLog
from services.permissions import admin_required, admin_or_auditor_required
from services.audit import create_audit_log


@login_required
def invoice_report(request):
    """Invoice report filtered by user's role/organisation."""
    user = request.user
    invoices = Invoice.objects.select_related('supplier', 'buyer')

    if user.is_supplier:
        invoices = invoices.filter(supplier=user.organisation)
    elif user.is_buyer:
        invoices = invoices.filter(buyer=user.organisation)
    elif user.is_financier:
        invoices = invoices.filter(offers__financier=user.organisation).distinct()
    # admin/compliance/auditor see all

    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    if request.GET.get('export') == 'csv':
        create_audit_log(user, 'report_exported', 'Invoice', '', request=request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invoice_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Reference', 'Supplier', 'Buyer', 'Amount', 'Currency', 'Status', 'Invoice Date', 'Due Date'])
        for inv in invoices:
            writer.writerow([inv.invoice_reference, inv.supplier.name, inv.buyer.name,
                           inv.invoice_amount, inv.currency, inv.status, inv.invoice_date, inv.due_date])
        return response

    return render(request, 'reports/invoice_report.html', {'invoices': invoices, 'status_filter': status_filter})


@login_required
def offer_report(request):
    user = request.user
    offers = FinancingOffer.objects.select_related('invoice', 'financier')

    if user.is_supplier:
        offers = offers.filter(invoice__supplier=user.organisation)
    elif user.is_financier:
        offers = offers.filter(financier=user.organisation)

    if request.GET.get('export') == 'csv':
        create_audit_log(user, 'report_exported', 'FinancingOffer', '', request=request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="offer_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice', 'Financier', 'Offered Amount', 'Discount Rate', 'Net Disbursement', 'Status'])
        for o in offers:
            writer.writerow([o.invoice.invoice_reference, o.financier.name, o.offered_amount,
                           o.discount_rate, o.net_disbursement, o.status])
        return response

    return render(request, 'reports/offer_report.html', {'offers': offers})


@login_required
def settlement_report(request):
    user = request.user
    settlements = Settlement.objects.select_related('invoice', 'supplier', 'financier')

    if user.is_supplier:
        settlements = settlements.filter(supplier=user.organisation)
    elif user.is_financier:
        settlements = settlements.filter(financier=user.organisation)

    if request.GET.get('export') == 'csv':
        create_audit_log(user, 'report_exported', 'Settlement', '', request=request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="settlement_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice', 'Supplier', 'Financier', 'Amount', 'Date', 'Reference', 'Status'])
        for s in settlements:
            writer.writerow([s.invoice.invoice_reference, s.supplier.name, s.financier.name,
                           s.settlement_amount, s.settlement_date, s.payment_reference, s.status])
        return response

    return render(request, 'reports/settlement_report.html', {'settlements': settlements})


@login_required
@admin_or_auditor_required
def audit_report(request):
    logs = AuditLog.objects.select_related('actor').all()[:500]

    if request.GET.get('export') == 'csv':
        create_audit_log(request.user, 'report_exported', 'AuditLog', '', request=request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Actor', 'Role', 'Action', 'Entity', 'Entity ID', 'IP'])
        for log in logs:
            writer.writerow([log.created_at, log.actor.email if log.actor else 'System',
                           log.actor_role, log.action, log.entity_type, log.entity_id, log.ip_address])
        return response

    return render(request, 'reports/audit_report.html', {'logs': logs})
