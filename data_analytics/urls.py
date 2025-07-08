from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/advanced/', views.dashboard_advanced, name='dashboard_advanced'),
]
