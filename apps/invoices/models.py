"""
Invoice Models - Invoice, InvoiceDocument, InvoiceStatusHistory
"""
import uuid
from datetime import date
from django.db import models
from django.conf import settings
from apps.organisations.models import Organisation


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_buyer_approval', 'Pending Buyer Approval'),
        ('clarification_requested', 'Clarification Requested'),
        ('approved_by_buyer', 'Approved by Buyer'),
        ('available_for_financing', 'Available for Financing'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('settlement_pending', 'Settlement Pending'),
        ('settled', 'Settled'),
        ('repayment_pending', 'Repayment Pending'),
        ('repaid', 'Repaid'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('ZWG', 'Zimbabwe Gold'),
        ('ZAR', 'South African Rand'),
        ('GBP', 'British Pound'),
        ('EUR', 'Euro'),
    ]
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('unrated', 'Unrated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_reference = models.CharField(max_length=30, unique=True, editable=False)
    supplier = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='supplier_invoices')
    buyer = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='buyer_invoices')
    invoice_number = models.CharField(max_length=100)
    purchase_order_number = models.CharField(max_length=100, blank=True)
    grn_number = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='USD')
    invoice_amount = models.DecimalField(max_digits=15, decimal_places=2)
    invoice_date = models.DateField()
    due_date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    risk_rating = models.CharField(max_length=20, choices=RISK_CHOICES, default='unrated')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='submitted_invoices'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['supplier', 'buyer', 'invoice_number']

    def __str__(self):
        return f"{self.invoice_reference} - {self.currency} {self.invoice_amount}"

    def save(self, *args, **kwargs):
        if not self.invoice_reference:
            self.invoice_reference = self.generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_reference():
        from django.utils import timezone
        year = timezone.now().year
        last = Invoice.objects.filter(
            invoice_reference__startswith=f'CZW-INV-{year}-'
        ).order_by('-invoice_reference').first()
        if last:
            try:
                last_num = int(last.invoice_reference.split('-')[-1])
            except (ValueError, IndexError):
                last_num = 0
            new_num = last_num + 1
        else:
            new_num = 1
        return f'CZW-INV-{year}-{new_num:06d}'

    @property
    def days_until_due(self):
        if self.due_date:
            return (self.due_date - date.today()).days
        return None

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < date.today()


def invoice_document_path(instance, filename):
    return f'secure_uploads/invoices/{instance.invoice.id}/{filename}'


class InvoiceDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('po', 'Purchase Order'),
        ('grn', 'Goods Received Note'),
        ('delivery_note', 'Delivery Note'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='invoice')
    file = models.FileField(upload_to=invoice_document_path)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_type}: {self.file_name}"


class InvoiceStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Invoice status histories'

    def __str__(self):
        return f"{self.invoice.invoice_reference}: {self.previous_status} → {self.new_status}"
