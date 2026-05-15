"""Invoice Views - Supplier invoice CRUD, buyer approval, financier marketplace."""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings as django_settings

from .models import Invoice, InvoiceDocument
from .forms import InvoiceForm, InvoiceDocumentForm
from apps.offers.models import FinancingOffer
from services.permissions import (
    supplier_required, buyer_required, financier_required,
    admin_required, organisation_approved_required, can_user_access_invoice
)
from services.workflows import (
    submit_invoice, approve_invoice, reject_invoice,
    request_invoice_clarification, submit_financing_offer, accept_offer, withdraw_offer
)
from services.audit import create_audit_log


# ─── Supplier Invoice Views ────────────────────────────────────

@login_required
@supplier_required
@organisation_approved_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, supplier_org=request.user.organisation)
        doc_form = InvoiceDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.supplier = request.user.organisation
            invoice.status = 'draft'
            invoice.save()

            # Handle document upload
            if request.FILES.get('file'):
                if doc_form.is_valid():
                    doc = doc_form.save(commit=False)
                    doc.invoice = invoice
                    doc.uploaded_by = request.user
                    doc.file_name = request.FILES['file'].name
                    doc.file_size = request.FILES['file'].size
                    doc.mime_type = request.FILES['file'].content_type or ''
                    # Validate file type
                    ext = os.path.splitext(doc.file_name)[1].lower()
                    if ext in django_settings.BLOCKED_UPLOAD_EXTENSIONS:
                        messages.error(request, 'This file type is not supported.')
                        invoice.delete()
                        return render(request, 'supplier/invoice_create.html', {'form': form, 'doc_form': doc_form})
                    if ext not in django_settings.ALLOWED_UPLOAD_EXTENSIONS:
                        messages.error(request, 'This file type is not supported.')
                        invoice.delete()
                        return render(request, 'supplier/invoice_create.html', {'form': form, 'doc_form': doc_form})
                    if doc.file_size > django_settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                        messages.error(request, f'File size exceeds the allowed limit ({django_settings.MAX_UPLOAD_SIZE_MB}MB).')
                        invoice.delete()
                        return render(request, 'supplier/invoice_create.html', {'form': form, 'doc_form': doc_form})
                    doc.save()
                    create_audit_log(request.user, 'document_uploaded', 'InvoiceDocument', str(doc.id), request=request)

            action = request.POST.get('action', 'draft')
            if action == 'submit':
                result = submit_invoice(invoice, request.user, request)
                if result['success']:
                    messages.success(request, f'Invoice {invoice.invoice_reference} submitted successfully.')
                else:
                    messages.warning(request, result['error'])
            else:
                messages.success(request, f'Invoice {invoice.invoice_reference} saved as draft.')

            return redirect('invoices:detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(supplier_org=request.user.organisation)
        doc_form = InvoiceDocumentForm()
    return render(request, 'supplier/invoice_create.html', {'form': form, 'doc_form': doc_form})


@login_required
@supplier_required
def invoice_list_supplier(request):
    invoices = Invoice.objects.filter(supplier=request.user.organisation)
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    return render(request, 'supplier/invoice_list.html', {'invoices': invoices, 'status_filter': status_filter})


@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if not can_user_access_invoice(request.user, invoice):
        messages.error(request, 'You do not have permission to view this invoice.')
        return redirect('dashboard:index')

    documents = invoice.documents.all()
    offers = invoice.offers.all() if (request.user.is_supplier and request.user.organisation == invoice.supplier) or request.user.is_admin else invoice.offers.none()
    status_history = invoice.status_history.all()

    # Financier sees only their own offers
    if request.user.is_financier:
        offers = invoice.offers.filter(financier=request.user.organisation)

    template = 'supplier/invoice_detail.html'
    if request.user.is_buyer:
        template = 'buyer/invoice_detail.html'
    elif request.user.is_financier:
        template = 'financier/invoice_detail.html'
    elif request.user.is_admin or request.user.is_compliance or request.user.is_auditor:
        template = 'admin_portal/invoice_detail.html'

    return render(request, template, {
        'invoice': invoice, 'documents': documents,
        'offers': offers, 'status_history': status_history,
    })


@login_required
@supplier_required
def invoice_submit(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, supplier=request.user.organisation)
    if request.method == 'POST':
        result = submit_invoice(invoice, request.user, request)
        if result['success']:
            messages.success(request, f'Invoice {invoice.invoice_reference} submitted successfully.')
        else:
            messages.error(request, result['error'])
    return redirect('invoices:detail', invoice_id=invoice.id)


@login_required
@supplier_required
def invoice_upload_doc(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, supplier=request.user.organisation)
    if request.method == 'POST':
        form = InvoiceDocumentForm(request.POST, request.FILES)
        if form.is_valid() and request.FILES.get('file'):
            doc = form.save(commit=False)
            doc.invoice = invoice
            doc.uploaded_by = request.user
            doc.file_name = request.FILES['file'].name
            doc.file_size = request.FILES['file'].size
            doc.mime_type = request.FILES['file'].content_type or ''
            ext = os.path.splitext(doc.file_name)[1].lower()
            if ext in django_settings.BLOCKED_UPLOAD_EXTENSIONS or ext not in django_settings.ALLOWED_UPLOAD_EXTENSIONS:
                messages.error(request, 'This file type is not supported.')
            elif doc.file_size > django_settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                messages.error(request, f'File size exceeds {django_settings.MAX_UPLOAD_SIZE_MB}MB limit.')
            else:
                doc.save()
                create_audit_log(request.user, 'document_uploaded', 'InvoiceDocument', str(doc.id), request=request)
                messages.success(request, 'Document uploaded.')
    return redirect('invoices:detail', invoice_id=invoice.id)


@login_required
def document_download(request, doc_id):
    doc = get_object_or_404(InvoiceDocument, id=doc_id)
    if not can_user_access_invoice(request.user, doc.invoice):
        raise Http404
    create_audit_log(request.user, 'document_downloaded', 'InvoiceDocument', str(doc.id), request=request)
    return FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.file_name)


# ─── Buyer Approval Views ──────────────────────────────────────

@login_required
@buyer_required
def buyer_pending_approvals(request):
    invoices = Invoice.objects.filter(
        buyer=request.user.organisation,
        status='pending_buyer_approval'
    )
    return render(request, 'buyer/pending_approvals.html', {'invoices': invoices})


@login_required
@buyer_required
def buyer_approve(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, buyer=request.user.organisation)
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comments = request.POST.get('comments', '')
        if decision == 'approve':
            result = approve_invoice(invoice, request.user, comments, request)
        elif decision == 'reject':
            result = reject_invoice(invoice, request.user, comments, request)
        elif decision == 'clarification':
            result = request_invoice_clarification(invoice, request.user, comments, request)
        else:
            result = {'success': False, 'error': 'Invalid decision.'}

        if result['success']:
            messages.success(request, f'Invoice {invoice.invoice_reference} has been {decision}d.')
        else:
            messages.error(request, result['error'])
    return redirect('invoices:detail', invoice_id=invoice.id)


@login_required
@buyer_required
def buyer_invoice_list(request):
    invoices = Invoice.objects.filter(buyer=request.user.organisation)
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    return render(request, 'buyer/invoice_list.html', {'invoices': invoices, 'status_filter': status_filter})


# ─── Financier Views ───────────────────────────────────────────

@login_required
@financier_required
@organisation_approved_required
def marketplace(request):
    invoices = Invoice.objects.filter(
        status__in=['available_for_financing', 'offer_received']
    ).select_related('supplier', 'buyer')
    return render(request, 'financier/marketplace.html', {'invoices': invoices})


@login_required
@financier_required
@organisation_approved_required
def submit_offer_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.status not in ('available_for_financing', 'offer_received'):
        messages.error(request, 'This invoice is not available for financing.')
        return redirect('invoices:marketplace')

    if request.method == 'POST':
        offer_data = {
            'advance_percentage': request.POST.get('advance_percentage', 90),
            'discount_rate': request.POST.get('discount_rate', 5),
            'tenor_days': request.POST.get('tenor_days', 30),
            'expiry_date': request.POST.get('expiry_date') or None,
            'terms': request.POST.get('terms', ''),
        }
        result = submit_financing_offer(invoice, request.user.organisation, request.user, offer_data, request)
        if result['success']:
            messages.success(request, 'Offer submitted successfully.')
            return redirect('invoices:financier_offers')
        else:
            messages.error(request, result['error'])

    return render(request, 'financier/submit_offer.html', {'invoice': invoice})


@login_required
@financier_required
def financier_offers(request):
    offers = FinancingOffer.objects.filter(
        financier=request.user.organisation
    ).select_related('invoice', 'invoice__supplier')
    return render(request, 'financier/my_offers.html', {'offers': offers})


@login_required
@financier_required
def offer_withdraw_view(request, offer_id):
    offer = get_object_or_404(FinancingOffer, id=offer_id, financier=request.user.organisation)
    if request.method == 'POST':
        result = withdraw_offer(offer, request.user, request)
        if result['success']:
            messages.success(request, 'Offer withdrawn.')
        else:
            messages.error(request, result['error'])
    return redirect('invoices:financier_offers')


# ─── Supplier Offer Acceptance ─────────────────────────────────

@login_required
@supplier_required
def supplier_offers(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, supplier=request.user.organisation)
    offers = invoice.offers.filter(status='submitted').select_related('financier')
    return render(request, 'supplier/offers.html', {'invoice': invoice, 'offers': offers})


@login_required
@supplier_required
def supplier_accept_offer(request, offer_id):
    offer = get_object_or_404(FinancingOffer, id=offer_id)
    if request.user.organisation != offer.invoice.supplier:
        messages.error(request, 'You can only accept offers on your own invoices.')
        return redirect('dashboard:index')
    if request.method == 'POST':
        result = accept_offer(offer, request.user, request)
        if result['success']:
            messages.success(request, 'Offer accepted successfully.')
        else:
            messages.error(request, result['error'])
    return redirect('invoices:detail', invoice_id=offer.invoice.id)


# ─── Admin Invoice Views ──────────────────────────────────────

@login_required
@admin_required
def admin_invoice_list(request):
    invoices = Invoice.objects.select_related('supplier', 'buyer').all()
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    return render(request, 'admin_portal/invoices/list.html', {'invoices': invoices, 'status_filter': status_filter})


@login_required
@admin_required
def admin_settlement_record(request, offer_id):
    offer = get_object_or_404(FinancingOffer, id=offer_id)
    if request.method == 'POST':
        from services.workflows import record_settlement
        settlement_data = {
            'settlement_amount': offer.net_disbursement,
            'settlement_date': request.POST.get('settlement_date'),
            'payment_reference': request.POST.get('payment_reference'),
            'settlement_method': request.POST.get('settlement_method', 'bank_transfer'),
            'notes': request.POST.get('notes', ''),
        }
        result = record_settlement(offer, request.user, settlement_data, request)
        if result['success']:
            messages.success(request, 'Settlement recorded successfully.')
            return redirect('invoices:detail', invoice_id=offer.invoice.id)
        else:
            messages.error(request, result['error'])
    return render(request, 'admin_portal/settlements/record.html', {'offer': offer})


@login_required
@admin_required
def admin_offer_list(request):
    offers = FinancingOffer.objects.select_related('invoice', 'financier').all()
    status_filter = request.GET.get('status', '')
    if status_filter:
        offers = offers.filter(status=status_filter)
    return render(request, 'admin_portal/offers/list.html', {'offers': offers, 'status_filter': status_filter})
