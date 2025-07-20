import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from activities.models import Actividad, RegistroHabito
from .models import AnalisisUsuario, MetricaHabitual, ReporteRendimiento, ComparacionUsuarios

@login_required
def dashboard(request):
    """Dashboard principal con métricas básicas del usuario"""
    user = request.user
    today = date.today()
    
    # Obtener o crear análisis del usuario
    analisis, created = AnalisisUsuario.objects.get_or_create(
        user=user,
        defaults={
            'fecha_analisis': today,
            'rendimiento_general': 0,
            'rendimiento_habitos': 0,
            'rendimiento_tareas': 0,
            'habitos_completados': 0,
            'total_habitos': 0,
            'tareas_completadas': 0,
            'total_tareas': 0,
            'dias_activo': 0,
            'racha_actual': 0,
            'mejor_racha': 0,
            'habitos_mejorar': []
        }
    )
    
    # Actualizar análisis si es necesario
    if created or analisis.fecha_analisis != today:
        actualizar_analisis_usuario(user)
        analisis.refresh_from_db()
    
    # Obtener métricas de hábitos con metas personalizadas
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    metricas_habitos = []
    
    for habito in habitos:
        dias_completados = habito.registros.filter(estado='completado').count()
        dias_totales = habito.meta_dias if habito.meta_dias else 30  # Usar meta personalizada o 30 días por defecto
        
        # Calcular porcentaje basado en la meta personalizada
        porcentaje = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        
        # Determinar si necesita mejora basado en la meta personalizada
        necesita_mejora = porcentaje < 60 and dias_completados < dias_totales * 0.6
        
        # Calcular tendencia
        ultimos_7_dias = habito.registros.filter(
            fecha__gte=today - timedelta(days=7),
            estado='completado'
        ).count()
        
        if ultimos_7_dias >= 5:
            tendencia = 'mejorando'
        elif ultimos_7_dias >= 3:
            tendencia = 'estable'
        else:
            tendencia = 'empeorando'
        
        metrica = {
            'habito': habito,
            'dias_completados': dias_completados,
            'dias_totales': dias_totales,
            'porcentaje_completado': porcentaje,
            'necesita_mejora': necesita_mejora,
            'tendencia': tendencia
        }
        metricas_habitos.append(metrica)
    
    # Preparar datos para el gráfico
    habitos_labels = [metrica['habito'].nombre for metrica in metricas_habitos]
    habitos_data = [metrica['porcentaje_completado'] for metrica in metricas_habitos]
    habitos_colors = []
    
    for metrica in metricas_habitos:
        if metrica['porcentaje_completado'] >= 80:
            habitos_colors.append('#28a745')  # Verde
        elif metrica['porcentaje_completado'] >= 60:
            habitos_colors.append('#ffc107')  # Amarillo
        else:
            habitos_colors.append('#dc3545')  # Rojo
    
    context = {
        'analisis': analisis,
        'metricas_habitos': metricas_habitos,
        'current_date': today,
        'habitos_labels_json': json.dumps(habitos_labels),
        'habitos_data_json': json.dumps(habitos_data),
        'habitos_colors_json': json.dumps(habitos_colors),
    }
    
    return render(request, 'data_analytics/dashboard.html', context)

@login_required
def dashboard_advanced(request):
    """Dashboard avanzado con análisis detallado y recomendaciones"""
    user = request.user
    today = date.today()
    
    # Obtener análisis actualizado
    analisis, created = AnalisisUsuario.objects.get_or_create(
        user=user,
        defaults={'fecha_analisis': today}
    )
    
    if created or analisis.fecha_analisis != today:
        actualizar_analisis_usuario(user)
        analisis.refresh_from_db()
    
    # Calcular tendencias basadas en metas personalizadas
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    tendencias = calcular_tendencias_avanzadas(user, habitos)
    
    # Generar recomendaciones personalizadas
    recomendaciones = generar_recomendaciones_personalizadas(user, analisis, habitos)
    
    context = {
        'analisis': analisis,
        'tendencias': tendencias,
        'recomendaciones': recomendaciones,
        'current_date': today,
    }
    
    return render(request, 'data_analytics/dashboard_advanced.html', context)

@login_required
def analisis_individual(request, user_id=None):
    """Análisis individual detallado"""
    if user_id:
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user
    
    # Verificar permisos - solo permitir ver análisis propio o ser admin
    if not request.user.is_staff and request.user != target_user:
        return render(request, 'data_analytics/error.html', {
            'message': 'No tienes permisos para ver este análisis.'
        })
    
    today = date.today()
    
    # Obtener o crear análisis
    analisis, created = AnalisisUsuario.objects.get_or_create(
        user=target_user,
        defaults={'fecha_analisis': today}
    )
    
    if created or analisis.fecha_analisis != today:
        actualizar_analisis_usuario(target_user)
        analisis.refresh_from_db()
    
    # Obtener reporte de rendimiento
    reporte, created = ReporteRendimiento.objects.get_or_create(
        user=target_user,
        fecha_inicio=today,
        defaults={
            'fecha_fin': today,
            'resumen': '',
            'areas_mejora': [],
            'logros': [],
            'puntuacion_general': 0,
            'recomendaciones': []
        }
    )
    
    if created:
        generar_reporte_rendimiento(target_user, analisis)
        reporte.refresh_from_db()
    
    # Análisis detallado de hábitos con metas personalizadas
    habitos = Actividad.objects.filter(user=target_user, tipo='habito')
    habitos_analisis = []
    
    for habito in habitos:
        dias_completados = habito.registros.filter(estado='completado').count()
        dias_totales = habito.meta_dias if habito.meta_dias else 30
        
        porcentaje = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        
        # Calcular tendencia
        ultimos_7_dias = habito.registros.filter(
            fecha__gte=today - timedelta(days=7),
            estado='completado'
        ).count()
        
        if ultimos_7_dias >= 5:
            tendencia = 'mejorando'
        elif ultimos_7_dias >= 3:
            tendencia = 'estable'
        else:
            tendencia = 'empeorando'
        
        habito_analisis = {
            'habito': habito,
            'dias_completados': dias_completados,
            'total_dias': dias_totales,
            'porcentaje': porcentaje,
            'tendencia': tendencia,
            'necesita_mejora': porcentaje < 60 and dias_completados < dias_totales * 0.6
        }
        habitos_analisis.append(habito_analisis)
    
    context = {
        'target_user': target_user,
        'analisis': analisis,
        'reporte': reporte,
        'habitos_analisis': habitos_analisis,
        'es_admin': request.user.is_staff,
        'current_date': today,
    }
    
    return render(request, 'data_analytics/analisis_individual.html', context)

@staff_member_required
def comparacion_usuarios(request):
    """Comparación de rendimiento entre usuarios (solo para administradores)"""
    today = timezone.now().date()
    
    # Obtener o crear comparación
    comparacion, created = ComparacionUsuarios.objects.get_or_create(
        fecha_comparacion=today,
        defaults={
            'total_usuarios_activos': 0,
            'promedio_rendimiento_general': 0,
            'promedio_habitos_completados': 0,
            'promedio_tareas_completadas': 0,
            'tendencia_general': 'estable',
            'usuarios_mejorando': [],
            'usuarios_necesitan_ayuda': []
        }
    )
    
    if created or comparacion.fecha_comparacion != today:
        actualizar_comparacion_usuarios()
        comparacion.refresh_from_db()
    
    # Obtener top usuarios y usuarios que necesitan ayuda
    top_usuarios = AnalisisUsuario.objects.filter(
        fecha_analisis=today,
        rendimiento_general__gte=80
    ).order_by('-rendimiento_general')[:5]
    
    usuarios_ayuda = AnalisisUsuario.objects.filter(
        fecha_analisis=today,
        rendimiento_general__lt=60
    ).order_by('rendimiento_general')[:5]
    
    context = {
        'comparacion': comparacion,
        'top_usuarios': top_usuarios,
        'usuarios_ayuda': usuarios_ayuda,
        'current_date': today,
    }
    
    return render(request, 'data_analytics/comparacion_usuarios.html', context)

def api_metricas_usuario(request):
    """API endpoint para obtener métricas del usuario en formato JSON"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
    
    user = request.user
    today = timezone.now().date()
    
    # Obtener análisis actualizado
    analisis, created = AnalisisUsuario.objects.get_or_create(
        user=user,
        defaults={'fecha_analisis': today}
    )
    
    if created or analisis.fecha_analisis != today:
        actualizar_analisis_usuario(user)
        analisis.refresh_from_db()
    
    # Obtener métricas de hábitos con metas personalizadas
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    habitos_metricas = []
    
    for habito in habitos:
        dias_completados = habito.registros.filter(estado='completado').count()
        dias_totales = habito.meta_dias if habito.meta_dias else 30
        
        porcentaje = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        
        habito_metrica = {
            'nombre': habito.nombre,
            'dias_completados': dias_completados,
            'meta_dias': dias_totales,
            'porcentaje_completado': round(porcentaje, 1),
            'necesita_mejora': porcentaje < 60
        }
        habitos_metricas.append(habito_metrica)
    
    data = {
        'usuario': user.username,
        'fecha_analisis': analisis.fecha_analisis.isoformat(),
        'rendimiento_general': analisis.rendimiento_general,
        'rendimiento_habitos': analisis.rendimiento_habitos,
        'rendimiento_tareas': analisis.rendimiento_tareas,
        'dias_activo': analisis.dias_activo,
        'racha_actual': analisis.racha_actual,
        'mejor_racha': analisis.mejor_racha,
        'habitos_metricas': habitos_metricas
    }
    
    return JsonResponse(data)

# Funciones auxiliares
def actualizar_analisis_usuario(user):
    """Actualizar análisis completo del usuario considerando metas personalizadas"""
    today = timezone.now().date()
    
    # Obtener hábitos y tareas
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    tareas = Actividad.objects.filter(user=user, tipo='tarea')
    
    # Calcular métricas de hábitos con metas personalizadas
    total_habitos = habitos.count()
    habitos_completados = 0
    rendimiento_habitos = 0
    
    if total_habitos > 0:
        for habito in habitos:
            dias_completados = habito.registros.filter(estado='completado').count()
            dias_totales = habito.meta_dias if habito.meta_dias else 30
            
            # Calcular progreso basado en la meta personalizada
            progreso = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
            habitos_completados += dias_completados
            rendimiento_habitos += progreso
        
        rendimiento_habitos = rendimiento_habitos / total_habitos
    
    # Calcular métricas de tareas
    total_tareas = tareas.count()
    tareas_completadas = tareas.filter(estado='completado').count()
    rendimiento_tareas = (tareas_completadas / total_tareas * 100) if total_tareas > 0 else 0
    
    # Calcular rendimiento general
    rendimiento_general = (rendimiento_habitos + rendimiento_tareas) / 2
    
    # Calcular días activo y rachas
    dias_activo = calcular_dias_activo(user)
    racha_actual, mejor_racha = calcular_rachas(user)
    
    # Identificar hábitos que necesitan mejora
    habitos_mejorar = []
    for habito in habitos:
        dias_completados = habito.registros.filter(estado='completado').count()
        dias_totales = habito.meta_dias if habito.meta_dias else 30
        progreso = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        
        if progreso < 60:
            habitos_mejorar.append(habito.nombre)
    
    # Actualizar o crear análisis
    analisis, created = AnalisisUsuario.objects.update_or_create(
        user=user,
        defaults={
            'fecha_analisis': today,
            'rendimiento_general': rendimiento_general,
            'rendimiento_habitos': rendimiento_habitos,
            'rendimiento_tareas': rendimiento_tareas,
            'habitos_completados': habitos_completados,
            'total_habitos': total_habitos,
            'tareas_completadas': tareas_completadas,
            'total_tareas': total_tareas,
            'dias_activo': dias_activo,
            'racha_actual': racha_actual,
            'mejor_racha': mejor_racha,
            'habitos_mejorar': habitos_mejorar
        }
    )
    
    return analisis

def calcular_tendencias_avanzadas(user, habitos):
    """Calcular tendencias avanzadas considerando metas personalizadas"""
    today = timezone.now().date()
    
    # Comparar rendimiento actual vs anterior
    analisis_actual = AnalisisUsuario.objects.filter(
        user=user,
        fecha_analisis=today
    ).first()
    
    analisis_anterior = AnalisisUsuario.objects.filter(
        user=user,
        fecha_analisis=today - timedelta(days=7)
    ).first()
    
    if analisis_actual and analisis_anterior:
        diferencia = analisis_actual.rendimiento_general - analisis_anterior.rendimiento_general
        
        if diferencia > 5:
            tendencia = 'mejorando'
            mensaje = f'Tu rendimiento ha mejorado {diferencia:.1f}% en la última semana'
        elif diferencia < -5:
            tendencia = 'empeorando'
            mensaje = f'Tu rendimiento ha disminuido {abs(diferencia):.1f}% en la última semana'
        else:
            tendencia = 'estable'
            mensaje = 'Tu rendimiento se mantiene estable'
    else:
        tendencia = 'insuficientes_datos'
        mensaje = 'Necesitamos más datos para calcular tendencias'
        diferencia = 0
    
    return {
        'tendencia': tendencia,
        'diferencia': diferencia,
        'mensaje': mensaje
    }

def generar_recomendaciones_personalizadas(user, analisis, habitos):
    """Generar recomendaciones personalizadas basadas en metas"""
    recomendaciones = []
    
    # Analizar hábitos con bajo rendimiento
    for habito in habitos:
        dias_completados = habito.registros.filter(estado='completado').count()
        dias_totales = habito.meta_dias if habito.meta_dias else 30
        progreso = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        
        if progreso < 50:
            recomendaciones.append({
                'titulo': f'Mejorar {habito.nombre}',
                'descripcion': f'Tu progreso en "{habito.nombre}" es del {progreso:.1f}%. Considera ajustar tu meta o aumentar la frecuencia.',
                'prioridad': 'alta'
            })
        elif progreso < 70:
            recomendaciones.append({
                'titulo': f'Consolidar {habito.nombre}',
                'descripcion': f'Estás en buen camino con "{habito.nombre}" ({progreso:.1f}%). Mantén la consistencia.',
                'prioridad': 'media'
            })
    
    # Recomendaciones generales
    if analisis.racha_actual < 3:
        recomendaciones.append({
            'titulo': 'Construir consistencia',
            'descripcion': 'Tu racha actual es corta. Intenta mantener al menos 3 días consecutivos.',
            'prioridad': 'alta'
        })
    
    if analisis.rendimiento_general < 60:
        recomendaciones.append({
            'titulo': 'Establecer metas más pequeñas',
            'descripcion': 'Considera reducir tus metas para hacerlas más alcanzables.',
            'prioridad': 'media'
        })
    
    return recomendaciones

def generar_reporte_rendimiento(user, analisis):
    """Generar reporte detallado de rendimiento"""
    today = timezone.now().date()
    
    # Crear resumen
    if analisis.rendimiento_general >= 80:
        resumen = "Excelente rendimiento general. Mantén este nivel de consistencia."
    elif analisis.rendimiento_general >= 60:
        resumen = "Buen rendimiento. Hay espacio para mejorar en algunas áreas."
    else:
        resumen = "Rendimiento necesita mejora. Enfócate en construir hábitos más consistentes."
    
    # Identificar áreas de mejora
    areas_mejora = []
    if analisis.rendimiento_habitos < 60:
        areas_mejora.append("Consistencia en hábitos")
    if analisis.rendimiento_tareas < 60:
        areas_mejora.append("Completar tareas pendientes")
    if analisis.racha_actual < 5:
        areas_mejora.append("Mantener rachas más largas")
    
    # Identificar logros
    logros = []
    if analisis.rendimiento_general >= 80:
        logros.append("Rendimiento general excelente")
    if analisis.racha_actual >= 7:
        logros.append(f"Racha actual de {analisis.racha_actual} días")
    if analisis.mejor_racha >= 30:
        logros.append(f"Mejor racha de {analisis.mejor_racha} días")
    
    # Calcular puntuación general
    puntuacion = min(10, (analisis.rendimiento_general / 10) + (analisis.racha_actual / 10) + 5)
    
    # Generar recomendaciones
    recomendaciones = []
    if analisis.rendimiento_habitos < 70:
        recomendaciones.append({
            'titulo': 'Mejorar consistencia en hábitos',
            'descripcion': 'Enfócate en completar tus hábitos diariamente',
            'prioridad': 'alta'
        })
    
    if analisis.racha_actual < 5:
        recomendaciones.append({
            'titulo': 'Construir rachas más largas',
            'descripcion': 'Intenta mantener al menos 5 días consecutivos',
            'prioridad': 'media'
        })
    
    # Crear o actualizar reporte
    ReporteRendimiento.objects.update_or_create(
        user=user,
        fecha_inicio=today,
        defaults={
            'fecha_fin': today,
            'resumen': resumen,
            'areas_mejora': areas_mejora,
            'logros': logros,
            'puntuacion_general': puntuacion,
            'recomendaciones': recomendaciones
        }
    )

def actualizar_comparacion_usuarios():
    """Actualizar comparación de usuarios"""
    today = timezone.now().date()
    
    # Obtener todos los análisis de hoy
    analisis_usuarios = AnalisisUsuario.objects.filter(fecha_analisis=today)
    
    if not analisis_usuarios.exists():
        return
    
    # Calcular promedios
    total_usuarios = analisis_usuarios.count()
    usuarios_activos = analisis_usuarios.filter(dias_activo__gt=0).count()
    
    promedio_rendimiento = analisis_usuarios.aggregate(
        avg_rendimiento=models.Avg('rendimiento_general')
    )['avg_rendimiento'] or 0
    
    promedio_habitos = analisis_usuarios.aggregate(
        avg_habitos=models.Avg('habitos_completados')
    )['avg_habitos'] or 0
    
    promedio_tareas = analisis_usuarios.aggregate(
        avg_tareas=models.Avg('tareas_completadas')
    )['avg_tareas'] or 0
    
    # Determinar tendencia general
    analisis_semana_pasada = AnalisisUsuario.objects.filter(
        fecha_analisis=today - timedelta(days=7)
    )
    
    if analisis_semana_pasada.exists():
        promedio_anterior = analisis_semana_pasada.aggregate(
            avg_rendimiento=models.Avg('rendimiento_general')
        )['avg_rendimiento'] or 0
        
        if promedio_rendimiento > promedio_anterior + 5:
            tendencia_general = 'positiva'
        elif promedio_rendimiento < promedio_anterior - 5:
            tendencia_general = 'negativa'
        else:
            tendencia_general = 'estable'
    else:
        tendencia_general = 'estable'
    
    # Identificar usuarios mejorando y necesitando ayuda
    usuarios_mejorando = []
    usuarios_necesitan_ayuda = []
    
    for analisis in analisis_usuarios:
        if analisis.rendimiento_general >= 80:
            usuarios_mejorando.append({
                'username': analisis.user.username,
                'rendimiento': analisis.rendimiento_general,
                'racha_actual': analisis.racha_actual
            })
        elif analisis.rendimiento_general < 60:
            usuarios_necesitan_ayuda.append({
                'username': analisis.user.username,
                'rendimiento': analisis.rendimiento_general,
                'habitos_mejorar': analisis.habitos_mejorar
            })
    
    # Actualizar comparación
    ComparacionUsuarios.objects.update_or_create(
        fecha_comparacion=today,
        defaults={
            'total_usuarios_activos': usuarios_activos,
            'promedio_rendimiento_general': promedio_rendimiento,
            'promedio_habitos_completados': promedio_habitos,
            'promedio_tareas_completadas': promedio_tareas,
            'tendencia_general': tendencia_general,
            'usuarios_mejorando': usuarios_mejorando,
            'usuarios_necesitan_ayuda': usuarios_necesitan_ayuda
        }
    )

def calcular_dias_activo(user):
    """Calcular días activo del usuario"""
    registros = RegistroHabito.objects.filter(habito__user=user)
    return registros.values('fecha').distinct().count()

def calcular_rachas(user):
    """Calcular racha actual y mejor racha"""
    registros = RegistroHabito.objects.filter(
        habito__user=user,
        estado='completado'
    ).order_by('fecha')
    
    if not registros.exists():
        return 0, 0
    
    # Calcular racha actual
    today = timezone.now().date()
    racha_actual = 0
    fecha_actual = today
    
    while True:
        if registros.filter(fecha=fecha_actual).exists():
            racha_actual += 1
            fecha_actual -= timedelta(days=1)
        else:
            break
    
    # Calcular mejor racha
    mejor_racha = 0
    racha_temp = 0
    fecha_anterior = None
    
    for registro in registros:
        if fecha_anterior is None or (registro.fecha - fecha_anterior).days == 1:
            racha_temp += 1
        else:
            mejor_racha = max(mejor_racha, racha_temp)
            racha_temp = 1
        fecha_anterior = registro.fecha
    
    mejor_racha = max(mejor_racha, racha_temp)
    
    return racha_actual, mejor_racha
