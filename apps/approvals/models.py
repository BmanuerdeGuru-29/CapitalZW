"""BuyerApproval Model"""
import uuid
from django.db import models
from django.conf import settings
from apps.organisations.models import Organisation
from apps.invoices.models import Invoice


class BuyerApproval(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('clarification_requested', 'Clarification Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='approvals')
    buyer = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name='buyer_approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    decision = models.CharField(max_length=30, choices=DECISION_CHOICES)
    comments = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice.invoice_reference} - {self.decision}"
