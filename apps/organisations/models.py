"""
Organisation Models - Organisation, SupplierProfile, BuyerProfile, FinancierProfile
"""
import uuid
from django.db import models


class Organisation(models.Model):
    TYPE_CHOICES = [
        ('supplier', 'Supplier'),
        ('buyer', 'Buyer'),
        ('financier', 'Financier'),
        ('platform', 'Platform'),
        ('partner', 'Partner'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('unrated', 'Unrated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    trading_name = models.CharField(max_length=255, blank=True)
    organisation_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Zimbabwe')
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_rating = models.CharField(max_length=20, choices=RISK_CHOICES, default='unrated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_suspended(self):
        return self.status == 'suspended'

    @property
    def can_transact(self):
        return self.status == 'approved'


class SupplierProfile(models.Model):
    VERIFICATION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='supplier_profile')
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    branch_name = models.CharField(max_length=255, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='pending')
    preferred_currency = models.CharField(max_length=10, default='USD')
    max_invoice_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Supplier: {self.organisation.name}"


class BuyerProfile(models.Model):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='buyer_profile')
    approval_required = models.BooleanField(default=True)
    approval_sla_days = models.IntegerField(default=5)
    buyer_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_terms_days = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Buyer: {self.organisation.name}"


class FinancierProfile(models.Model):
    TYPE_CHOICES = [
        ('bank', 'Bank'),
        ('mfi', 'Microfinance Institution'),
        ('investor', 'Investor'),
        ('fund', 'Fund'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
    ]

    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='financier_profile')
    licence_number = models.CharField(max_length=100, blank=True)
    financier_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    maximum_exposure = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    default_discount_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Financier: {self.organisation.name}"
