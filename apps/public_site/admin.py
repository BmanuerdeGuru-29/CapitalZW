from django.contrib import admin
from .models import ContactEnquiry

@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'organisation_type', 'created_at')
    list_filter = ('organisation_type',)
