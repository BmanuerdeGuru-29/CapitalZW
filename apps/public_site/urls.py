from django.urls import path
from . import views

app_name = 'public_site'

urlpatterns = [
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('for-suppliers/', views.for_suppliers, name='for_suppliers'),
    path('for-buyers/', views.for_buyers, name='for_buyers'),
    path('for-financiers/', views.for_financiers, name='for_financiers'),
    path('pricing/', views.pricing, name='pricing'),
    path('contact/', views.contact, name='contact'),
]
