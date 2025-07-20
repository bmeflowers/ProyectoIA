from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.activities, name='activities'),
    path('agregar/', views.agregar_actividad, name='agregar_actividad'),
    path('editar/<int:pk>/', views.editar_actividad, name='editar_actividad'),
    path('eliminar/<int:pk>/', views.eliminar_actividad, name='eliminar_actividad'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado, name='cambiar_estado'),
    path('registrar-habito/<int:pk>/', views.registrar_habito, name='registrar_habito'),
]
