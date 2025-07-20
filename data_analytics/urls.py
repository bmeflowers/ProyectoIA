from django.urls import path
from . import views

app_name = 'data_analytics'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/advanced/', views.dashboard_advanced, name='dashboard_advanced'),
    path('analisis/individual/', views.analisis_individual, name='analisis_individual'),
    path('analisis/individual/<int:user_id>/', views.analisis_individual, name='analisis_individual_user'),
    path('comparacion/usuarios/', views.comparacion_usuarios, name='comparacion_usuarios'),
    path('api/metricas/', views.api_metricas_usuario, name='api_metricas'),
    path('generar-documento/', views.generar_documento_analisis, name='generar_documento'),
]
