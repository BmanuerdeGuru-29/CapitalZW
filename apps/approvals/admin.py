from django.contrib import admin
from .models import BuyerApproval

@admin.register(BuyerApproval)
class BuyerApprovalAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'buyer', 'approver', 'decision', 'decided_at')
    list_filter = ('decision',)
