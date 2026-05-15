"""Public Site Models"""
import uuid
from django.db import models


class ContactEnquiry(models.Model):
    TYPE_CHOICES = [
        ('supplier', 'Supplier'),
        ('buyer', 'Buyer'),
        ('financier', 'Financier'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    organisation_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    organisation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    interest_area = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contact Enquiries'

    def __str__(self):
        return f"{self.full_name} - {self.email}"
