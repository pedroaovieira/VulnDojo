from django.urls import path
from . import views

app_name = 'cve_repository_api'

urlpatterns = [
    path('', views.CVEListAPIView.as_view(), name='cve-list'),
    path('<str:cve_id>/', views.CVEDetailAPIView.as_view(), name='cve-detail'),
    path('stats/', views.cve_stats, name='cve-stats'),
]