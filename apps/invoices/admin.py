from django.contrib import admin
from .models import Invoice, InvoiceDocument, InvoiceStatusHistory


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_reference', 'supplier', 'buyer', 'currency', 'invoice_amount', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('invoice_reference', 'invoice_number')
    readonly_fields = ('invoice_reference',)


@admin.register(InvoiceDocument)
class InvoiceDocumentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'document_type', 'file_name', 'file_size', 'created_at')


@admin.register(InvoiceStatusHistory)
class InvoiceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'previous_status', 'new_status', 'changed_by', 'created_at')
