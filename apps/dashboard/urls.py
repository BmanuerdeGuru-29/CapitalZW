from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('supplier/', views.supplier_dashboard, name='supplier'),
    path('buyer/', views.buyer_dashboard, name='buyer'),
    path('financier/', views.financier_dashboard, name='financier'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('compliance/', views.compliance_dashboard, name='compliance'),
    path('auditor/', views.auditor_dashboard, name='auditor'),
]
