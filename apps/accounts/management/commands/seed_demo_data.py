import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.organisations.models import Organisation, SupplierProfile, BuyerProfile, FinancierProfile
from apps.invoices.models import Invoice

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with demo data for CapitalZW'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing demo data...')
        
        # In a real scenario we'd be careful, but this is a demo seeder
        Invoice.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        Organisation.objects.all().delete()

        self.stdout.write('Creating organisations...')

        # 1. Supplier
        supplier_org = Organisation.objects.create(
            name='Acme Manufacturing',
            trading_name='Acme Man',
            organisation_type='supplier',
            registration_number='REG-1001',
            sector='Manufacturing',
            city='Harare',
            country='ZW',
            contact_email='contact@acme.co.zw',
            status='approved'
        )
        SupplierProfile.objects.create(organisation=supplier_org)

        # 2. Buyer
        buyer_org = Organisation.objects.create(
            name='MegaCorp Retail',
            trading_name='MegaCorp',
            organisation_type='buyer',
            registration_number='REG-2001',
            sector='Retail',
            city='Harare',
            country='ZW',
            contact_email='accounts@megacorp.co.zw',
            status='approved'
        )
        BuyerProfile.objects.create(organisation=buyer_org)

        # 3. Financier
        financier_org = Organisation.objects.create(
            name='Capital Finance Bank',
            trading_name='CF Bank',
            organisation_type='financier',
            registration_number='REG-3001',
            sector='Banking',
            city='Bulawayo',
            country='ZW',
            contact_email='info@cfbank.co.zw',
            status='approved'
        )
        FinancierProfile.objects.create(organisation=financier_org)

        self.stdout.write('Creating users...')

        # Admin User
        admin_user = User.objects.create_user(
            email='admin@capitalzw.co.zw',
            password='password123',
            first_name='System',
            last_name='Admin',
            role='platform_admin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )

        # Supplier User
        supplier_user = User.objects.create_user(
            email='supplier@acme.co.zw',
            password='password123',
            first_name='John',
            last_name='Supplier',
            role='supplier_admin',
            organisation=supplier_org,
            is_active=True
        )

        # Buyer User
        buyer_user = User.objects.create_user(
            email='buyer@megacorp.co.zw',
            password='password123',
            first_name='Jane',
            last_name='Buyer',
            role='buyer_admin',
            organisation=buyer_org,
            is_active=True
        )

        # Financier User
        financier_user = User.objects.create_user(
            email='financier@cfbank.co.zw',
            password='password123',
            first_name='Bob',
            last_name='Banker',
            role='financier_admin',
            organisation=financier_org,
            is_active=True
        )

        self.stdout.write('Creating demo invoices...')
        
        now = timezone.now().date()
        
        # 1. Draft Invoice
        Invoice.objects.create(
            invoice_reference='INV-ACME-001',
            supplier=supplier_org,
            buyer=buyer_org,
            invoice_number='INV-2024-001',
            currency='USD',
            invoice_amount=Decimal('5000.00'),
            invoice_date=now - timedelta(days=2),
            due_date=now + timedelta(days=30),
            status='draft'
        )

        # 2. Pending Approval Invoice
        Invoice.objects.create(
            invoice_reference='INV-ACME-002',
            supplier=supplier_org,
            buyer=buyer_org,
            invoice_number='INV-2024-002',
            currency='USD',
            invoice_amount=Decimal('12500.00'),
            invoice_date=now - timedelta(days=5),
            due_date=now + timedelta(days=25),
            status='pending_buyer_approval',
            submitted_by=supplier_user,
            submitted_at=timezone.now() - timedelta(days=1)
        )

        # 3. Available for Financing Invoice (Approved by Buyer)
        Invoice.objects.create(
            invoice_reference='INV-ACME-003',
            supplier=supplier_org,
            buyer=buyer_org,
            invoice_number='INV-2024-003',
            currency='USD',
            invoice_amount=Decimal('45000.00'),
            invoice_date=now - timedelta(days=10),
            due_date=now + timedelta(days=50),
            status='available_for_financing',
            submitted_by=supplier_user,
            submitted_at=timezone.now() - timedelta(days=5),
            approved_at=timezone.now() - timedelta(days=2)
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write('Login Credentials (password for all: password123):')
        self.stdout.write(f'  Admin:     {admin_user.email}')
        self.stdout.write(f'  Supplier:  {supplier_user.email}')
        self.stdout.write(f'  Buyer:     {buyer_user.email}')
        self.stdout.write(f'  Financier: {financier_user.email}')
