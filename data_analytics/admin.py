from django.contrib import admin
from .models import AnalisisUsuario, MetricaHabitual, ReporteRendimiento, ComparacionUsuarios

@admin.register(AnalisisUsuario)
class AnalisisUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rendimiento_general', 'rendimiento_habitos', 'rendimiento_tareas', 'dias_activo', 'racha_actual', 'fecha_analisis')
    list_filter = ('fecha_analisis', 'rendimiento_general')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('fecha_analisis',)
    ordering = ('-fecha_analisis',)
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'fecha_analisis')
        }),
        ('Métricas Generales', {
            'fields': ('total_habitos', 'total_tareas', 'habitos_completados', 'tareas_completadas')
        }),
        ('Rendimiento', {
            'fields': ('rendimiento_habitos', 'rendimiento_tareas', 'rendimiento_general')
        }),
        ('Análisis Temporal', {
            'fields': ('dias_activo', 'racha_actual', 'mejor_racha')
        }),
        ('Hábitos que Necesitan Mejora', {
            'fields': ('habitos_bajo_rendimiento', 'habitos_mejorar'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MetricaHabitual)
class MetricaHabitualAdmin(admin.ModelAdmin):
    list_display = ('habito', 'analisis', 'porcentaje_completado', 'tendencia', 'necesita_mejora')
    list_filter = ('tendencia', 'necesita_mejora', 'analisis__fecha_analisis')
    search_fields = ('habito__nombre', 'analisis__user__username')
    readonly_fields = ('dias_completados', 'dias_totales', 'porcentaje_completado')
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('analisis', 'habito')
        }),
        ('Métricas', {
            'fields': ('dias_completados', 'dias_totales', 'porcentaje_completado')
        }),
        ('Análisis', {
            'fields': ('tendencia', 'necesita_mejora', 'recomendacion')
        }),
    )

@admin.register(ReporteRendimiento)
class ReporteRendimientoAdmin(admin.ModelAdmin):
    list_display = ('user', 'fecha_inicio', 'fecha_fin', 'puntuacion_general', 'fecha_generado')
    list_filter = ('fecha_generado', 'puntuacion_general')
    search_fields = ('user__username', 'resumen')
    readonly_fields = ('fecha_generado',)
    ordering = ('-fecha_generado',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'fecha_inicio', 'fecha_fin', 'fecha_generado')
        }),
        ('Contenido del Reporte', {
            'fields': ('resumen', 'puntuacion_general')
        }),
        ('Análisis Detallado', {
            'fields': ('areas_mejora', 'logros', 'recomendaciones'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ComparacionUsuarios)
class ComparacionUsuariosAdmin(admin.ModelAdmin):
    list_display = ('fecha_analisis', 'total_usuarios_activos', 'promedio_rendimiento_general', 'tendencia_general')
    list_filter = ('fecha_analisis', 'tendencia_general')
    readonly_fields = ('fecha_analisis',)
    ordering = ('-fecha_analisis',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('fecha_analisis', 'total_usuarios_activos', 'tendencia_general')
        }),
        ('Estadísticas Promedio', {
            'fields': ('promedio_rendimiento_general', 'promedio_habitos_completados', 'promedio_tareas_completadas')
        }),
        ('Rankings', {
            'fields': ('top_usuarios', 'usuarios_mejorando', 'usuarios_necesitan_ayuda'),
            'classes': ('collapse',)
        }),
    )
