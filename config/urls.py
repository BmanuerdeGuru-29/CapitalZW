"""
CapitalZW Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public website
    path('', include('apps.public_site.urls')),

    # Authentication
    path('auth/', include('apps.accounts.urls')),

    # Dashboard
    path('dashboard/', include('apps.dashboard.urls')),

    # Organisations (admin management)
    path('organisations/', include('apps.organisations.urls')),

    # Invoices (all roles)
    path('invoices/', include('apps.invoices.urls')),

    # Notifications
    path('notifications/', include('apps.notifications.urls')),

    # Audit logs
    path('audit/', include('apps.audit.urls')),

    # Reports
    path('reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customisation
admin.site.site_header = 'CapitalZW Administration'
admin.site.site_title = 'CapitalZW Admin'
admin.site.index_title = 'Platform Administration'
