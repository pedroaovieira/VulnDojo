from django.urls import path
from . import views

app_name = 'cve_repository'

urlpatterns = [
    path('', views.cve_list, name='cve-list'),
    path('<str:cve_id>/', views.cve_detail, name='cve-detail'),
]