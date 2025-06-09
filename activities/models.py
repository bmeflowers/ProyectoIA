from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Actividad(models.Model):
    TIPO_CHOICES = [
        ('tarea', 'Tarea'),
        ('habito', 'Hábito'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con User
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_limite = models.DateField(null=True, blank=True)  # Solo para tareas
    hora_habito = models.TimeField(null=True, blank=True)   # Solo para hábitos
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class RegistroHabito(models.Model):
    habito = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=Actividad.ESTADO_CHOICES)

    class Meta:
        unique_together = ('habito', 'fecha')