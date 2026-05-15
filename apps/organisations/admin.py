from django.contrib import admin
from .models import Organisation, SupplierProfile, BuyerProfile, FinancierProfile


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation_type', 'status', 'city', 'country', 'created_at')
    list_filter = ('organisation_type', 'status', 'risk_rating')
    search_fields = ('name', 'trading_name', 'registration_number')


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'verification_status', 'preferred_currency')


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'payment_terms_days', 'approval_required')


@admin.register(FinancierProfile)
class FinancierProfileAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'financier_type', 'status')
