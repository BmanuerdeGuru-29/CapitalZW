from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pending/', views.pending_view, name='pending'),
    path('suspended/', views.suspended_view, name='suspended'),
    path('profile/', views.profile_view, name='profile'),
    # Admin user management
    path('users/', views.user_list_view, name='user_list'),
    path('users/<uuid:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<uuid:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<uuid:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
]
