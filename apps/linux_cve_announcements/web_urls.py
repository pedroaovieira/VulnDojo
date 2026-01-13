from django.urls import path
from . import views

app_name = 'linux_cve_announcements'

urlpatterns = [
    path('', views.announcement_list, name='announcement-list'),
    path('<str:message_id>/', views.announcement_detail, name='announcement-detail'),
]