from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Supplier
    path('create/', views.invoice_create, name='create'),
    path('my/', views.invoice_list_supplier, name='supplier_list'),
    path('<uuid:invoice_id>/', views.invoice_detail, name='detail'),
    path('<uuid:invoice_id>/submit/', views.invoice_submit, name='submit'),
    path('<uuid:invoice_id>/upload-doc/', views.invoice_upload_doc, name='upload_doc'),
    path('<uuid:invoice_id>/offers/', views.supplier_offers, name='supplier_offers'),
    path('document/<uuid:doc_id>/download/', views.document_download, name='doc_download'),

    # Buyer
    path('buyer/', views.buyer_invoice_list, name='buyer_list'),
    path('buyer/pending/', views.buyer_pending_approvals, name='buyer_pending'),
    path('<uuid:invoice_id>/approve/', views.buyer_approve, name='buyer_approve'),

    # Financier
    path('marketplace/', views.marketplace, name='marketplace'),
    path('<uuid:invoice_id>/submit-offer/', views.submit_offer_view, name='submit_offer'),
    path('offers/my/', views.financier_offers, name='financier_offers'),
    path('offers/<uuid:offer_id>/withdraw/', views.offer_withdraw_view, name='offer_withdraw'),
    path('offers/<uuid:offer_id>/accept/', views.supplier_accept_offer, name='accept_offer'),

    # Admin
    path('admin/all/', views.admin_invoice_list, name='admin_list'),
    path('admin/offers/', views.admin_offer_list, name='admin_offers'),
    path('admin/offers/<uuid:offer_id>/settle/', views.admin_settlement_record, name='admin_settle'),
]
