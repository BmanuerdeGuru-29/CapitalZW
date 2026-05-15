from django.urls import path
from . import views

app_name = 'organisations'

urlpatterns = [
    path('', views.org_list_view, name='list'),
    path('<uuid:org_id>/', views.org_detail_view, name='detail'),
    path('<uuid:org_id>/approve/', views.org_approve_view, name='approve'),
    path('<uuid:org_id>/reject/', views.org_reject_view, name='reject'),
    path('<uuid:org_id>/suspend/', views.org_suspend_view, name='suspend'),
]
