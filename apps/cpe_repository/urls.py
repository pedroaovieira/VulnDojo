from django.urls import path
from . import views

app_name = 'cpe_repository_api'

urlpatterns = [
    path('', views.CPEListAPIView.as_view(), name='cpe-list'),
    path('<str:cpe_name_id>/', views.CPEDetailAPIView.as_view(), name='cpe-detail'),
    path('stats/', views.cpe_stats, name='cpe-stats'),
]