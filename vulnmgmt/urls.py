"""
URL configuration for vulnmgmt project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('api/cpe/', include('apps.cpe_repository.urls')),
    path('api/cve/', include('apps.cve_repository.urls')),
    path('api/linux-cve/', include('apps.linux_cve_announcements.urls')),
    path('cpe/', include('apps.cpe_repository.web_urls')),
    path('cve/', include('apps.cve_repository.web_urls')),
    path('linux-cve/', include('apps.linux_cve_announcements.web_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)