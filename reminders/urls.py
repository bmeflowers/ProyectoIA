from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('send/', views.enviar_notificacion, name='enviar_notificacion'),
    path('recordatorio/', views.enviar_recordatorio_habitos_pendientes, name='recordatorio_habitos'),
    path('notificacion-automatica/', views.notificacion_automatica, name='notificacion_automatica'),
    path('motivacion-manana/', views.notificacion_motivacion_manana, name='motivacion_manana'),
    path('recordatorio-mediodia/', views.notificacion_recordatorio_mediodia, name='recordatorio_mediodia'),
    path('motivacion-tarde/', views.notificacion_motivacion_tarde, name='motivacion_tarde'),
    path('recordatorio-noche/', views.notificacion_recordatorio_noche, name='recordatorio_noche'),
    path('celebracion/', views.notificacion_celebracion, name='celebracion'),
    path('notificacion-horario/', views.notificacion_automatica_por_horario, name='notificacion_horario'),
    path('tareas-automatica/', views.notificacion_tareas_automatica, name='tareas_automatica'),
]
