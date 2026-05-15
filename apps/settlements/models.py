"""Settlement and Repayment Models"""
import uuid
from django.db import models
from django.conf import settings
from apps.organisations.models import Organisation
from apps.invoices.models import Invoice
from apps.offers.models import FinancingOffer


class Settlement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ]
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('manual', 'Manual'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='settlements')
    offer = models.ForeignKey(FinancingOffer, on_delete=models.CASCADE, related_name='settlements')
    supplier = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='supplier_settlements')
    financier = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='financier_settlements')
    settlement_amount = models.DecimalField(max_digits=15, decimal_places=2)
    settlement_date = models.DateField()
    payment_reference = models.CharField(max_length=255)
    settlement_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Settlement: {self.invoice.invoice_reference} - {self.settlement_amount}"


class Repayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('defaulted', 'Defaulted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='repayments')
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, related_name='repayments')
    payer = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='repayments_made')
    financier = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='repayments_received')
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Repayment: {self.invoice.invoice_reference} - {self.amount_due}"
