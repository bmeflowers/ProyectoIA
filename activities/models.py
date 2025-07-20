from django.db import models
from django.contrib.auth.models import User

class Actividad(models.Model):
    TIPO_CHOICES = [
        ('tarea', 'Tarea'),
        ('habito', 'Hábito'),
    ]
    
    icono = models.CharField(max_length=5, blank=True, null=True)
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_limite = models.DateField(null=True, blank=True)
    hora_habito = models.TimeField(null=True, blank=True)
    dias_semana = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Aquí agregamos la meta personalizada para días de hábito
    meta_dias = models.PositiveIntegerField(
        default=150, 
        blank=True, 
        null=True,
        help_text="Número de días meta para completar este hábito"
    )

    def __str__(self):
        return self.nombre

    def es_habito(self):
        return self.tipo == 'habito'

    def es_tarea(self):
        return self.tipo == 'tarea'

class RegistroHabito(models.Model):
    habito = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='registros')
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=Actividad.ESTADO_CHOICES)

    class Meta:
        unique_together = ('habito', 'fecha')

    def save(self, *args, **kwargs):
        if not self.habito.es_habito():
            raise ValueError("Solo se pueden registrar hábitos en RegistroHabito.")
        super().save(*args, **kwargs)
