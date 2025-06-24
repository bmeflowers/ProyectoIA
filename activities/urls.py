from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('activities/', views.activities, name='activities'),
    path('activities/agregar/', views.agregar_actividad, name='agregar_actividad'),
    path('activities/eliminar/<int:pk>/', views.eliminar_actividad, name='eliminar_actividad'),
    path('activities/tarea/estado/<int:pk>/', views.cambiar_estado, name='cambiar_estado'),
    path('activities/habito/registrar/<int:pk>/', views.registrar_habito, name='registrar_habito'),
]
