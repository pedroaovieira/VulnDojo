from django.urls import path
from . import views

app_name = 'cpe_repository'

urlpatterns = [
    path('', views.cpe_list, name='cpe-list'),
    path('<str:cpe_name_id>/', views.cpe_detail, name='cpe-detail'),
]