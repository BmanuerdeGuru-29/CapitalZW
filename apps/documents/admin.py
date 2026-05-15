from django.contrib import admin
from .models import KYCDocument

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'document_type', 'status', 'uploaded_by', 'created_at')
    list_filter = ('status', 'document_type')
