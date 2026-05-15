"""Notification Model"""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('offer', 'Offer'),
        ('settlement', 'Settlement'),
        ('system', 'System'),
        ('approval', 'Approval'),
        ('kyc', 'KYC'),
        ('dispute', 'Dispute'),
    ]
    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='in_app')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_entity_type = models.CharField(max_length=50, blank=True)
    related_entity_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.user.email}"
