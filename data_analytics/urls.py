from django.urls import path
from . import views

app_name = 'data_analytics'


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/advanced/', views.dashboard_advanced, name='dashboard_advanced'),
]
