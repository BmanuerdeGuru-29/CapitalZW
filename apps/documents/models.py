"""KYC Document Model"""
import uuid
from django.db import models
from django.conf import settings
from apps.organisations.models import Organisation


def kyc_document_path(instance, filename):
    return f'secure_uploads/kyc/{instance.organisation.id}/{filename}'


class KYCDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('registration', 'Company Registration'),
        ('tax_clearance', 'Tax Clearance'),
        ('id_document', 'ID Document'),
        ('proof_of_address', 'Proof of Address'),
        ('bank_statement', 'Bank Statement'),
        ('licence', 'Licence'),
        ('financial_statement', 'Financial Statement'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='kyc_documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_kyc_docs')
    document_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to=kyc_document_path)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_kyc_docs'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'KYC Document'

    def __str__(self):
        return f"{self.organisation.name} - {self.get_document_type_display()}"
