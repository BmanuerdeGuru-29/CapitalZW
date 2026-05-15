"""FinancingOffer Model"""
import uuid
from django.db import models
from django.conf import settings
from apps.organisations.models import Organisation
from apps.invoices.models import Invoice


class FinancingOffer(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('withdrawn', 'Withdrawn'),
        ('expired', 'Expired'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('settled', 'Settled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='offers')
    financier = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='financing_offers')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    # Offer terms
    offered_amount = models.DecimalField(max_digits=15, decimal_places=2)
    advance_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text='Percentage of invoice amount')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Annual discount rate %')
    platform_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    financier_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Calculated fields
    net_disbursement = models.DecimalField(max_digits=15, decimal_places=2,
        help_text='offered_amount - platform_fee - financier_fee')
    repayment_amount = models.DecimalField(max_digits=15, decimal_places=2,
        help_text='Amount buyer/supplier repays to financier')
    tenor_days = models.IntegerField(default=30, help_text='Finance tenor in days')
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    terms = models.TextField(blank=True, help_text='Additional terms and conditions')
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Offer {self.financier.name} → {self.invoice.invoice_reference}: {self.offered_amount}"
