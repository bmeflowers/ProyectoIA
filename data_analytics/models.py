from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from activities.models import Actividad, RegistroHabito

class AnalisisUsuario(models.Model):
    """Modelo para almacenar análisis de rendimiento de usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    
    # Métricas generales
    total_habitos = models.IntegerField(default=0)
    total_tareas = models.IntegerField(default=0)
    habitos_completados = models.IntegerField(default=0)
    tareas_completadas = models.IntegerField(default=0)
    
    # Porcentajes de rendimiento
    rendimiento_habitos = models.FloatField(default=0.0)  # Porcentaje
    rendimiento_tareas = models.FloatField(default=0.0)   # Porcentaje
    rendimiento_general = models.FloatField(default=0.0)  # Promedio general
    
    # Análisis temporal
    dias_activo = models.IntegerField(default=0)
    racha_actual = models.IntegerField(default=0)
    mejor_racha = models.IntegerField(default=0)
    
    # Hábitos que necesitan mejora
    habitos_bajo_rendimiento = models.JSONField(default=list)
    habitos_mejorar = models.JSONField(default=list)
    
    class Meta:
        ordering = ['-fecha_analisis']
    
    def __str__(self):
        return f"Análisis de {self.user.username} - {self.fecha_analisis.strftime('%Y-%m-%d')}"

class MetricaHabitual(models.Model):
    """Métricas específicas por hábito"""
    analisis = models.ForeignKey(AnalisisUsuario, on_delete=models.CASCADE)
    habito = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    
    # Métricas del hábito
    dias_completados = models.IntegerField(default=0)
    dias_totales = models.IntegerField(default=0)
    porcentaje_completado = models.FloatField(default=0.0)
    
    # Análisis de tendencia
    tendencia = models.CharField(max_length=20, choices=[
        ('mejorando', 'Mejorando'),
        ('estable', 'Estable'),
        ('empeorando', 'Empeorando'),
        ('nuevo', 'Nuevo'),
    ], default='nuevo')
    
    # Recomendaciones
    necesita_mejora = models.BooleanField(default=False)
    recomendacion = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('analisis', 'habito')
    
    def __str__(self):
        return f"{self.habito.nombre} - {self.porcentaje_completado}%"

class ReporteRendimiento(models.Model):
    """Reportes detallados de rendimiento"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_generado = models.DateTimeField(auto_now_add=True)
    
    # Resumen ejecutivo
    resumen = models.TextField()
    
    # Áreas de mejora
    areas_mejora = models.JSONField(default=list)
    
    # Logros destacados
    logros = models.JSONField(default=list)
    
    # Recomendaciones personalizadas
    recomendaciones = models.JSONField(default=list)
    
    # Puntuación general (1-10)
    puntuacion_general = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-fecha_generado']
    
    def __str__(self):
        return f"Reporte {self.user.username} {self.fecha_inicio} - {self.fecha_fin}"

class ComparacionUsuarios(models.Model):
    """Comparación de rendimiento entre usuarios (para análisis grupal)"""
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    
    # Estadísticas generales
    total_usuarios_activos = models.IntegerField(default=0)
    promedio_rendimiento_general = models.FloatField(default=0.0)
    promedio_habitos_completados = models.FloatField(default=0.0)
    promedio_tareas_completadas = models.FloatField(default=0.0)
    
    # Rankings
    top_usuarios = models.JSONField(default=list)
    usuarios_mejorando = models.JSONField(default=list)
    usuarios_necesitan_ayuda = models.JSONField(default=list)
    
    # Análisis de tendencias
    tendencia_general = models.CharField(max_length=20, choices=[
        ('positiva', 'Positiva'),
        ('estable', 'Estable'),
        ('negativa', 'Negativa'),
    ], default='estable')
    
    def __str__(self):
        return f"Comparación usuarios - {self.fecha_analisis.strftime('%Y-%m-%d')}"
