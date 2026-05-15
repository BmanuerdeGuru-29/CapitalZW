from django.contrib import admin
from .models import Settlement, Repayment

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'offer', 'settlement_amount', 'status', 'settlement_date')
    list_filter = ('status',)

@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'payer', 'financier', 'amount_due', 'amount_paid', 'status')
    list_filter = ('status',)
