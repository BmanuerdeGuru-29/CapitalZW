from django.contrib import admin
from .models import FinancingOffer

@admin.register(FinancingOffer)
class FinancingOfferAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'financier', 'offered_amount', 'discount_rate', 'status', 'created_at')
    list_filter = ('status',)
