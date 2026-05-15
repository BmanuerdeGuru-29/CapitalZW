from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('invoices/', views.invoice_report, name='invoices'),
    path('offers/', views.offer_report, name='offers'),
    path('settlements/', views.settlement_report, name='settlements'),
    path('audit/', views.audit_report, name='audit'),
]
