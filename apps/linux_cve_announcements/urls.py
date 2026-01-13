from django.urls import path
from . import views

app_name = 'linux_cve_announcements_api'

urlpatterns = [
    path('', views.LinuxCVEAnnouncementListAPIView.as_view(), name='announcement-list'),
    path('<str:message_id>/', views.LinuxCVEAnnouncementDetailAPIView.as_view(), name='announcement-detail'),
    path('stats/', views.linux_cve_stats, name='announcement-stats'),
]