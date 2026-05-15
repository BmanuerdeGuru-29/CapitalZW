"""
CapitalZW Accounts App - Custom User Model with Email Login
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = settings.USER_ROLES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='supplier_user')
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_supplier(self):
        return self.role in settings.SUPPLIER_ROLES

    @property
    def is_buyer(self):
        return self.role in settings.BUYER_ROLES

    @property
    def is_financier(self):
        return self.role in settings.FINANCIER_ROLES

    @property
    def is_admin(self):
        return self.role in settings.ADMIN_ROLES

    @property
    def is_compliance(self):
        return self.role in settings.COMPLIANCE_ROLES

    @property
    def is_auditor(self):
        return self.role in settings.AUDITOR_ROLES

    @property
    def role_group(self):
        if self.is_supplier:
            return 'supplier'
        elif self.is_buyer:
            return 'buyer'
        elif self.is_financier:
            return 'financier'
        elif self.is_admin:
            return 'admin'
        elif self.is_compliance:
            return 'compliance'
        elif self.is_auditor:
            return 'auditor'
        return 'unknown'

    @property
    def dashboard_url(self):
        from django.urls import reverse
        role_urls = {
            'supplier': 'dashboard:supplier',
            'buyer': 'dashboard:buyer',
            'financier': 'dashboard:financier',
            'admin': 'dashboard:admin',
            'compliance': 'dashboard:compliance',
            'auditor': 'dashboard:auditor',
        }
        url_name = role_urls.get(self.role_group, 'dashboard:supplier')
        return reverse(url_name)
