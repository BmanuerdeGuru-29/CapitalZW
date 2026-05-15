"""
Core Workflow Services - Business logic for the invoice finance lifecycle.

All major workflow actions are implemented here rather than in views.
Each function validates, transitions state, creates audit logs and notifications.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.invoices.models import Invoice, InvoiceStatusHistory
from apps.approvals.models import BuyerApproval
from apps.offers.models import FinancingOffer
from apps.settlements.models import Settlement, Repayment
from services.audit import create_audit_log
from services.notifications import create_notification, notify_org_users


def _create_status_history(invoice, old_status, new_status, user, comment=''):
    InvoiceStatusHistory.objects.create(
        invoice=invoice,
        previous_status=old_status,
        new_status=new_status,
        changed_by=user,
        comment=comment,
    )


# ─── Invoice Workflow ───────────────────────────────────────────

def submit_invoice(invoice, user, request=None):
    """Submit a draft invoice for buyer approval."""
    if invoice.status not in ('draft', 'clarification_requested'):
        return {'success': False, 'error': 'Invoice cannot be submitted in its current status.'}
    if not invoice.supplier.is_approved:
        return {'success': False, 'error': 'Your organisation must be approved before submitting invoices.'}
    if invoice.documents.count() == 0:
        return {'success': False, 'error': 'At least one document must be uploaded before submission.'}

    old_status = invoice.status
    with transaction.atomic():
        invoice.status = 'pending_buyer_approval'
        invoice.submitted_by = user
        invoice.submitted_at = timezone.now()
        invoice.save(update_fields=['status', 'submitted_by', 'submitted_at', 'updated_at'])
        _create_status_history(invoice, old_status, 'pending_buyer_approval', user, 'Invoice submitted')
        create_audit_log(user, 'invoice_submitted', 'Invoice', str(invoice.id), request=request)
        notify_org_users(
            invoice.buyer, 'Invoice Pending Approval',
            f'Invoice {invoice.invoice_reference} from {invoice.supplier.name} requires approval.',
            'approval', invoice
        )
    return {'success': True}


def approve_invoice(invoice, approver, comments='', request=None):
    """Buyer approves an invoice, making it available for financing."""
    if invoice.status != 'pending_buyer_approval':
        return {'success': False, 'error': 'Invoice is not pending approval.'}
    if approver.organisation != invoice.buyer:
        return {'success': False, 'error': 'You can only approve invoices assigned to your organisation.'}

    old_status = invoice.status
    with transaction.atomic():
        BuyerApproval.objects.create(
            invoice=invoice, buyer=invoice.buyer, approver=approver,
            decision='approved', comments=comments, decided_at=timezone.now(),
        )
        invoice.status = 'available_for_financing'
        invoice.approved_at = timezone.now()
        invoice.save(update_fields=['status', 'approved_at', 'updated_at'])
        _create_status_history(invoice, old_status, 'available_for_financing', approver, comments or 'Approved')
        create_audit_log(approver, 'invoice_approved', 'Invoice', str(invoice.id), request=request)
        notify_org_users(
            invoice.supplier, 'Invoice Approved',
            f'Invoice {invoice.invoice_reference} has been approved by {invoice.buyer.name}.',
            'invoice', invoice
        )
    return {'success': True}


def reject_invoice(invoice, approver, comments, request=None):
    """Buyer rejects an invoice."""
    if invoice.status != 'pending_buyer_approval':
        return {'success': False, 'error': 'Invoice is not pending approval.'}
    if not comments:
        return {'success': False, 'error': 'Please provide a reason for rejection.'}

    old_status = invoice.status
    with transaction.atomic():
        BuyerApproval.objects.create(
            invoice=invoice, buyer=invoice.buyer, approver=approver,
            decision='rejected', comments=comments, decided_at=timezone.now(),
        )
        invoice.status = 'rejected'
        invoice.save(update_fields=['status', 'updated_at'])
        _create_status_history(invoice, old_status, 'rejected', approver, comments)
        create_audit_log(approver, 'invoice_rejected', 'Invoice', str(invoice.id), request=request)
        notify_org_users(
            invoice.supplier, 'Invoice Rejected',
            f'Invoice {invoice.invoice_reference} has been rejected. Reason: {comments}',
            'invoice', invoice
        )
    return {'success': True}


def request_invoice_clarification(invoice, approver, comments, request=None):
    """Buyer requests clarification on an invoice."""
    if invoice.status != 'pending_buyer_approval':
        return {'success': False, 'error': 'Invoice is not pending approval.'}
    if not comments:
        return {'success': False, 'error': 'Please provide details for the clarification request.'}

    old_status = invoice.status
    with transaction.atomic():
        BuyerApproval.objects.create(
            invoice=invoice, buyer=invoice.buyer, approver=approver,
            decision='clarification_requested', comments=comments, decided_at=timezone.now(),
        )
        invoice.status = 'clarification_requested'
        invoice.save(update_fields=['status', 'updated_at'])
        _create_status_history(invoice, old_status, 'clarification_requested', approver, comments)
        create_audit_log(approver, 'clarification_requested', 'Invoice', str(invoice.id), request=request)
        notify_org_users(
            invoice.supplier, 'Clarification Requested',
            f'The buyer has requested clarification on invoice {invoice.invoice_reference}: {comments}',
            'invoice', invoice
        )
    return {'success': True}


# ─── Financing Offer Workflow ────────────────────────────────────

def submit_financing_offer(invoice, financier_org, user, offer_data, request=None):
    """Financier submits an offer on an available invoice.

    Offer calculations:
    - offered_amount = invoice_amount * (advance_percentage / 100)
    - finance_cost = offered_amount * (discount_rate / 100) * (tenor_days / 365)
    - platform_fee = offered_amount * 0.01 (1% platform fee for MVP)
    - financier_fee = finance_cost
    - net_disbursement = offered_amount - platform_fee - financier_fee
    - repayment_amount = offered_amount + finance_cost
    """
    if invoice.status not in ('available_for_financing', 'offer_received'):
        return {'success': False, 'error': 'Invoice is not available for financing.'}
    if not financier_org.is_approved:
        return {'success': False, 'error': 'Your organisation must be approved to submit offers.'}
    if FinancingOffer.objects.filter(invoice=invoice, financier=financier_org, status='submitted').exists():
        return {'success': False, 'error': 'You already have an active offer on this invoice.'}

    advance_pct = Decimal(str(offer_data.get('advance_percentage', 90)))
    discount_rate = Decimal(str(offer_data.get('discount_rate', 5)))
    tenor_days = int(offer_data.get('tenor_days', 30))

    offered_amount = invoice.invoice_amount * (advance_pct / Decimal('100'))
    finance_cost = offered_amount * (discount_rate / Decimal('100')) * (Decimal(tenor_days) / Decimal('365'))
    platform_fee = offered_amount * Decimal('0.01')  # 1% platform fee
    financier_fee = finance_cost
    net_disbursement = offered_amount - platform_fee - financier_fee
    repayment_amount = offered_amount + finance_cost

    with transaction.atomic():
        offer = FinancingOffer.objects.create(
            invoice=invoice,
            financier=financier_org,
            submitted_by=user,
            offered_amount=offered_amount.quantize(Decimal('0.01')),
            advance_percentage=advance_pct,
            discount_rate=discount_rate,
            platform_fee=platform_fee.quantize(Decimal('0.01')),
            financier_fee=financier_fee.quantize(Decimal('0.01')),
            net_disbursement=net_disbursement.quantize(Decimal('0.01')),
            repayment_amount=repayment_amount.quantize(Decimal('0.01')),
            tenor_days=tenor_days,
            expiry_date=offer_data.get('expiry_date'),
            terms=offer_data.get('terms', ''),
        )
        if invoice.status == 'available_for_financing':
            old_status = invoice.status
            invoice.status = 'offer_received'
            invoice.save(update_fields=['status', 'updated_at'])
            _create_status_history(invoice, old_status, 'offer_received', user, 'Offer received')

        create_audit_log(user, 'offer_submitted', 'FinancingOffer', str(offer.id), request=request)
        notify_org_users(
            invoice.supplier, 'New Financing Offer',
            f'A financing offer has been submitted for invoice {invoice.invoice_reference} by {financier_org.name}.',
            'offer', offer
        )
    return {'success': True, 'offer': offer}


def withdraw_offer(offer, user, request=None):
    """Financier withdraws their offer."""
    if offer.status != 'submitted':
        return {'success': False, 'error': 'Only submitted offers can be withdrawn.'}
    if user.organisation != offer.financier:
        return {'success': False, 'error': 'You can only withdraw your own offers.'}

    with transaction.atomic():
        offer.status = 'withdrawn'
        offer.save(update_fields=['status', 'updated_at'])
        create_audit_log(user, 'offer_withdrawn', 'FinancingOffer', str(offer.id), request=request)
    return {'success': True}


def accept_offer(offer, supplier_user, request=None):
    """Supplier accepts a financing offer. Rejects all other active offers on the same invoice."""
    if offer.status != 'submitted':
        return {'success': False, 'error': 'This offer cannot be accepted.'}
    if supplier_user.organisation != offer.invoice.supplier:
        return {'success': False, 'error': 'You can only accept offers on your own invoices.'}

    invoice = offer.invoice
    old_status = invoice.status

    with transaction.atomic():
        # Accept this offer
        offer.status = 'accepted'
        offer.accepted_at = timezone.now()
        offer.save(update_fields=['status', 'accepted_at', 'updated_at'])

        # Reject other active offers
        other_offers = FinancingOffer.objects.filter(
            invoice=invoice, status='submitted'
        ).exclude(id=offer.id)
        for other in other_offers:
            other.status = 'rejected'
            other.save(update_fields=['status', 'updated_at'])
            notify_org_users(
                other.financier, 'Offer Not Accepted',
                f'Your offer on invoice {invoice.invoice_reference} was not accepted.',
                'offer', other
            )

        # Update invoice status
        invoice.status = 'settlement_pending'
        invoice.save(update_fields=['status', 'updated_at'])
        _create_status_history(invoice, old_status, 'settlement_pending', supplier_user, 'Offer accepted')

        create_audit_log(supplier_user, 'offer_accepted', 'FinancingOffer', str(offer.id), request=request)
        notify_org_users(
            offer.financier, 'Offer Accepted',
            f'Your offer on invoice {invoice.invoice_reference} has been accepted by {invoice.supplier.name}.',
            'offer', offer
        )
        # Notify admins
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for admin_user in User.objects.filter(role__in=settings.ADMIN_ROLES, is_active=True):
            create_notification(
                admin_user, 'Offer Accepted - Settlement Required',
                f'Offer accepted on {invoice.invoice_reference}. Settlement recording required.',
                'settlement', offer
            )
    return {'success': True}


# ─── Settlement & Repayment ─────────────────────────────────────

def record_settlement(offer, user, settlement_data, request=None):
    """Admin records a settlement for an accepted offer."""
    if offer.status != 'accepted':
        return {'success': False, 'error': 'Settlement can only be recorded for accepted offers.'}

    invoice = offer.invoice
    old_status = invoice.status

    with transaction.atomic():
        settlement = Settlement.objects.create(
            invoice=invoice,
            offer=offer,
            supplier=invoice.supplier,
            financier=offer.financier,
            settlement_amount=settlement_data['settlement_amount'],
            settlement_date=settlement_data['settlement_date'],
            payment_reference=settlement_data['payment_reference'],
            settlement_method=settlement_data.get('settlement_method', 'bank_transfer'),
            status='completed',
            recorded_by=user,
            notes=settlement_data.get('notes', ''),
        )
        # Create repayment record
        Repayment.objects.create(
            invoice=invoice,
            settlement=settlement,
            payer=invoice.buyer,
            financier=offer.financier,
            amount_due=offer.repayment_amount,
            due_date=invoice.due_date,
            status='pending',
            recorded_by=user,
        )
        offer.status = 'settled'
        offer.save(update_fields=['status', 'updated_at'])
        invoice.status = 'settled'
        invoice.save(update_fields=['status', 'updated_at'])
        _create_status_history(invoice, old_status, 'settled', user, 'Settlement recorded')

        create_audit_log(user, 'settlement_recorded', 'Settlement', str(settlement.id), request=request)
        notify_org_users(invoice.supplier, 'Settlement Recorded',
            f'Settlement for invoice {invoice.invoice_reference} has been recorded.', 'settlement', settlement)
        notify_org_users(offer.financier, 'Settlement Recorded',
            f'Settlement for invoice {invoice.invoice_reference} has been recorded.', 'settlement', settlement)
    return {'success': True, 'settlement': settlement}


def record_repayment(repayment, user, payment_data, request=None):
    """Record a repayment against a settlement."""
    with transaction.atomic():
        repayment.amount_paid = payment_data['amount_paid']
        repayment.payment_date = payment_data.get('payment_date', timezone.now().date())
        repayment.payment_reference = payment_data.get('payment_reference', '')
        if repayment.amount_paid >= repayment.amount_due:
            repayment.status = 'paid'
        else:
            repayment.status = 'partial'
        repayment.recorded_by = user
        repayment.save()

        if repayment.status == 'paid':
            invoice = repayment.invoice
            old_status = invoice.status
            invoice.status = 'repaid'
            invoice.closed_at = timezone.now()
            invoice.save(update_fields=['status', 'closed_at', 'updated_at'])
            _create_status_history(invoice, old_status, 'repaid', user, 'Repayment completed')

        create_audit_log(user, 'repayment_recorded', 'Repayment', str(repayment.id), request=request)
    return {'success': True}
