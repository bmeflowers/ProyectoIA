import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
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
        dias_totales = habito.meta_dias if habito.meta_dias else 30
        
        # Calcular porcentaje basado en la meta personalizada
        porcentaje = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
        porcentaje = min(porcentaje, 100)  # Limitar al 100%
        
        # Determinar si necesita mejora basado en la meta personalizada
        necesita_mejora = porcentaje < 60 and dias_completados < dias_totales * 0.6
        
        # Calcular tendencia (últimos 7 días vs días anteriores)
        ultimos_7_dias = habito.registros.filter(
            fecha__gte=today - timedelta(days=7),
            estado='completado'
        ).count()
        
        # Calcular promedio de días anteriores para comparar
        dias_anteriores = habito.registros.filter(
            fecha__lt=today - timedelta(days=7),
            estado='completado'
        ).count()
        dias_anteriores_promedio = dias_anteriores / 7 if dias_anteriores > 0 else 0
        
        if ultimos_7_dias > dias_anteriores_promedio + 1:
            tendencia = 'mejorando'
        elif ultimos_7_dias >= dias_anteriores_promedio - 1:
            tendencia = 'estable'
        else:
            tendencia = 'empeorando'
        
        metrica = {
            'habito': habito,
            'dias_completados': dias_completados,
            'dias_totales': dias_totales,
            'porcentaje_completado': porcentaje,
            'necesita_mejora': necesita_mejora,
            'tendencia': tendencia,
            'ultimos_7_dias': ultimos_7_dias
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
    
    # Calcular suma de días completados y suma de metas
    suma_dias_completados = 0
    suma_metas = 0
    for habito in habitos:
        suma_dias_completados += habito.registros.filter(estado='completado').count()
        suma_metas += habito.meta_dias if habito.meta_dias else 30

    context = {
        'analisis': analisis,
        'metricas_habitos': metricas_habitos,
        'current_date': today,
        'habitos_labels_json': json.dumps(habitos_labels),
        'habitos_data_json': json.dumps(habitos_data),
        'habitos_colors_json': json.dumps(habitos_colors),
        'current_date': today,
        'suma_dias_completados': suma_dias_completados,
        'suma_metas': suma_metas,
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

        # Calcular porcentaje de avance en los últimos 7 días
        fecha_hoy = today
        fecha_7 = today - timedelta(days=6)
        fecha_14 = today - timedelta(days=13)
        # Últimos 7 días
        completados_ultimos_7 = habito.registros.filter(
            fecha__gte=fecha_7,
            fecha__lte=fecha_hoy,
            estado='completado'
        ).count()
        porcentaje_ultimos_7 = (completados_ultimos_7 / 7) * 100
        # 7 días anteriores
        completados_anteriores_7 = habito.registros.filter(
            fecha__gte=fecha_14,
            fecha__lt=fecha_7,
            estado='completado'
        ).count()
        porcentaje_anteriores_7 = (completados_anteriores_7 / 7) * 100
        # Comparar porcentajes
        diferencia = porcentaje_ultimos_7 - porcentaje_anteriores_7
        if diferencia > 10:
            tendencia = 'mejorando'
        elif diferencia < -10:
            tendencia = 'empeorando'
        else:
            tendencia = 'estable'

        habito_analisis = {
            'habito': habito,
            'dias_completados': dias_completados,
            'total_dias': dias_totales,
            'porcentaje': porcentaje,
            'tendencia': tendencia,
            'necesita_mejora': False  # Ya no se usa
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
        fecha_analisis=today,
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
    
    if created or comparacion.fecha_analisis != today:
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
        return HttpResponse({'error': 'Usuario no autenticado'}, status=401)
    
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
        'habitos_metricas': habitos_metricas
    }
    
    return HttpResponse(json.dumps(data))

@login_required
def generar_documento_analisis(request):
    """Genera un documento PDF con el análisis completo de hábitos del usuario"""
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
    
    # Obtener hábitos del usuario
    habitos = Actividad.objects.filter(user=user, tipo='habito')
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
            tendencia = 'Mejorando'
        elif ultimos_7_dias >= 3:
            tendencia = 'Estable'
        else:
            tendencia = 'Necesita mejora'
        
        habitos_analisis.append({
            'nombre': habito.nombre,
            'dias_completados': dias_completados,
            'dias_totales': dias_totales,
            'porcentaje': round(porcentaje, 1),
            'tendencia': tendencia,
            'meta_dias': habito.meta_dias or 30
        })
    
    # Crear el documento PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analisis_habitos_{user.username}_{today.strftime("%Y%m%d")}.pdf"'
    
    # Crear el documento
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#23AFAF')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    # Título del documento
    story.append(Paragraph("¡Bienvenido a tu informe de hábitos!", title_style))
    story.append(Spacer(1, 20))

    # Frase inspiradora inicial
    story.append(Paragraph("Recuerda: 'El éxito es la suma de pequeños esfuerzos repetidos día tras día.'", normal_style))
    story.append(Spacer(1, 20))

    # Mensaje introductorio
    story.append(Paragraph(f"¡Hola {user.username}! Este documento celebra tu constancia y dedicación. Cada paso cuenta y cada día suma. ¡Sigue avanzando con energía y optimismo!", normal_style))
    story.append(Spacer(1, 20))

    # Información del usuario
    story.append(Paragraph(f"Fecha del análisis: {today.strftime('%d/%m/%Y')}", normal_style))
    story.append(Spacer(1, 20))

    # Resumen ejecutivo
    story.append(Paragraph("¿Cómo vas en general?", subtitle_style))
    story.append(Paragraph(f"Rendimiento general: {analisis.rendimiento_general:.1f}%", normal_style))
    story.append(Paragraph(f"Días con hábitos completados: {analisis.habitos_completados}", normal_style))
    story.append(Paragraph(f"Días activo: {analisis.dias_activo}", normal_style))
    story.append(Spacer(1, 20))

    # Gráfica de barras de hábitos
    if habitos_analisis:
        from reportlab.graphics.shapes import Drawing, String, Rect
        from reportlab.graphics.charts.barcharts import HorizontalBarChart
        from reportlab.lib.colors import HexColor
        story.append(Paragraph("Tu progreso en cada hábito (visual)", subtitle_style))
        drawing = Drawing(400, 30 + 30 * len(habitos_analisis))
        bar = HorizontalBarChart()
        bar.x = 80
        bar.y = 10
        bar.height = 20 * len(habitos_analisis)
        bar.width = 250
        bar.data = [[habito['porcentaje'] for habito in habitos_analisis]]
        bar.strokeColor = colors.black
        bar.valueAxis.valueMin = 0
        bar.valueAxis.valueMax = 100
        bar.valueAxis.valueStep = 20
        bar.categoryAxis.categoryNames = [habito['nombre'] for habito in habitos_analisis]
        bar.bars[0].fillColor = HexColor('#2377af')
        drawing.add(bar)
        # Etiquetas de porcentaje
        for i, habito in enumerate(habitos_analisis):
            drawing.add(String(340, 20 * i + 15, f"{habito['porcentaje']}%", fontSize=10, fillColor=colors.black))
        story.append(drawing)
        story.append(Spacer(1, 20))

    # Análisis detallado de hábitos
    if habitos_analisis:
        story.append(Paragraph("Tu progreso hábito por hábito", subtitle_style))
        for habito in habitos_analisis:
            story.append(Paragraph(f"<b>{habito['nombre']}</b> - {habito['porcentaje']}% completado", normal_style))
            if habito['porcentaje'] >= 80:
                story.append(Paragraph("¡Increíble! Tu constancia es admirable. Sigue así, vas por el camino del éxito.", normal_style))
            elif habito['porcentaje'] >= 50:
                story.append(Paragraph("¡Muy bien! Vas por buen camino, cada día suma. Mantén el ritmo y verás grandes resultados.", normal_style))
            else:
                story.append(Paragraph("¡Ánimo! Cada pequeño avance cuenta. Lo importante es no rendirse y seguir intentándolo.", normal_style))
            story.append(Spacer(1, 8))
    story.append(Spacer(1, 20))

    # Recomendaciones
    story.append(Paragraph("¡Sigue creciendo!", subtitle_style))
    if analisis.rendimiento_general < 60:
        story.append(Paragraph("Recuerda que lo importante es no rendirse. Te sugerimos:", normal_style))
        story.append(Paragraph("- Ponte metas pequeñas y celebra cada logro", normal_style))
        story.append(Paragraph("- Usa recordatorios para no olvidar tus hábitos", normal_style))
        story.append(Paragraph("- Comparte tus avances con alguien cercano", normal_style))
    elif analisis.rendimiento_general < 80:
        story.append(Paragraph("¡Vas por buen camino! Para seguir mejorando:", normal_style))
        story.append(Paragraph("- Mantén tu ritmo y no te presiones", normal_style))
        story.append(Paragraph("- Si puedes, suma un nuevo hábito sencillo", normal_style))
        story.append(Paragraph("- Recuerda que cada día cuenta", normal_style))
    else:
        story.append(Paragraph("¡Felicidades! Tu esfuerzo se nota. Para mantenerlo:", normal_style))
        story.append(Paragraph("- Sigue con tu rutina, vas genial", normal_style))
        story.append(Paragraph("- Si quieres, desafíate con algo nuevo", normal_style))
        story.append(Paragraph("- Inspira a otros con tu ejemplo", normal_style))
    story.append(Spacer(1, 20))

    # Metas para el próximo período
    story.append(Paragraph("¿Qué podrías intentar la próxima semana?", subtitle_style))
    story.append(Paragraph("- Intenta sumar un día más de constancia", normal_style))
    story.append(Paragraph("- Ajusta tus metas si lo necesitas, ¡no pasa nada!", normal_style))
    story.append(Paragraph("- Recuerda que cada paso suma", normal_style))
    story.append(Spacer(1, 30))

    # Frase inspiradora final
    story.append(Paragraph("'La constancia es el secreto del éxito. ¡Sigue brillando!'", normal_style))
    story.append(Spacer(1, 10))

    # Pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph("Gracias por confiar en SoulTrack. ¡Tú puedes lograrlo!", footer_style))
    story.append(Paragraph(f"Documento generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    # Construir el documento
    doc.build(story)
    
    return response

# Funciones auxiliares
def validar_y_limpiar_datos(user):
    """Validar y limpiar datos inconsistentes del usuario"""
    today = timezone.now().date()
    
    # Verificar registros duplicados
    registros_duplicados = RegistroHabito.objects.filter(
        habito__user=user
    ).values('habito', 'fecha').annotate(
        count=models.Count('id')
    ).filter(count__gt=1)
    
    if registros_duplicados.exists():
        # Eliminar duplicados manteniendo solo el más reciente
        for duplicado in registros_duplicados:
            registros = RegistroHabito.objects.filter(
                habito_id=duplicado['habito'],
                fecha=duplicado['fecha']
            ).order_by('-id')
            
            # Mantener solo el primer registro, eliminar los demás
            for registro in registros[1:]:
                registro.delete()
    
    # Verificar registros con fechas futuras
    registros_futuros = RegistroHabito.objects.filter(
        habito__user=user,
        fecha__gt=today
    )
    
    if registros_futuros.exists():
        registros_futuros.delete()
    
    # Verificar hábitos sin registros pero marcados como completados
    habitos_sin_registros = Actividad.objects.filter(
        user=user,
        tipo='habito',
        estado='completado'
    ).exclude(
        registros__estado='completado'
    )
    
    for habito in habitos_sin_registros:
        habito.estado = 'pendiente'
        habito.save()
    
    return True

def actualizar_analisis_usuario(user):
    """Actualizar análisis completo del usuario considerando metas personalizadas"""
    # Primero validar y limpiar datos
    validar_y_limpiar_datos(user)
    
    today = timezone.now().date()
    
    # Obtener hábitos y tareas
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    tareas = Actividad.objects.filter(user=user, tipo='tarea')
    
    # Calcular métricas de hábitos con metas personalizadas
    total_habitos = habitos.count()
    habitos_completados = 0
    rendimiento_habitos = 0
    
    if total_habitos > 0:
        progresos_habitos = []
        for habito in habitos:
            dias_completados = habito.registros.filter(estado='completado').count()
            dias_totales = habito.meta_dias if habito.meta_dias else 30
            
            # Calcular progreso basado en la meta personalizada
            progreso = (dias_completados / dias_totales * 100) if dias_totales > 0 else 0
            progreso = min(progreso, 100)  # Limitar al 100%
            
            habitos_completados += dias_completados
            progresos_habitos.append(progreso)
        
        # Calcular rendimiento promedio de hábitos
        rendimiento_habitos = sum(progresos_habitos) / len(progresos_habitos) if progresos_habitos else 0
    
    # Calcular métricas de tareas
    total_tareas = tareas.count()
    tareas_completadas = tareas.filter(estado='completado').count()
    rendimiento_tareas = (tareas_completadas / total_tareas * 100) if total_tareas > 0 else 0
    
    # Calcular rendimiento general (promedio ponderado)
    if total_habitos > 0 and total_tareas > 0:
        rendimiento_general = (rendimiento_habitos + rendimiento_tareas) / 2
    elif total_habitos > 0:
        rendimiento_general = rendimiento_habitos
    elif total_tareas > 0:
        rendimiento_general = rendimiento_tareas
    else:
        rendimiento_general = 0
    
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
    """Actualizar comparación de rendimiento entre usuarios"""
    today = timezone.now().date()
    
    # Obtener análisis de usuarios activos (últimos 30 días)
    fecha_limite = today - timedelta(days=30)
    analisis_usuarios = AnalisisUsuario.objects.filter(
        fecha_analisis__gte=fecha_limite
    ).select_related('user')
    
    if not analisis_usuarios.exists():
        return
    
    # Calcular estadísticas generales
    usuarios_activos = analisis_usuarios.values('user').distinct().count()
    
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
        fecha_analisis=today,
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
    today = timezone.now().date()
    # Obtener todas las fechas en las que el usuario completó al menos un hábito
    fechas_con_registro = (
        RegistroHabito.objects.filter(
            habito__user=user,
            estado='completado'
        )
        .values_list('fecha', flat=True)
        .distinct()
    )
    if not fechas_con_registro:
        return 0, 0
    fechas_ordenadas = sorted(fechas_con_registro)
    # Calcular racha actual (hasta hoy)
    racha_actual = 0
    fecha_actual = today
    while fecha_actual in fechas_ordenadas:
        racha_actual += 1
        fecha_actual -= timedelta(days=1)
    # Calcular mejor racha histórica
    mejor_racha = 1
    racha_temp = 1
    for i in range(1, len(fechas_ordenadas)):
        if (fechas_ordenadas[i] - fechas_ordenadas[i-1]).days == 1:
            racha_temp += 1
        else:
            mejor_racha = max(mejor_racha, racha_temp)
            racha_temp = 1
    mejor_racha = max(mejor_racha, racha_temp)
    return racha_actual, mejor_racha

def detectar_errores_analisis(user):
    """Detectar y reportar errores en el análisis de datos del usuario"""
    errores = []
    warnings = []
    
    today = timezone.now().date()
    
    # Verificar análisis existente
    analisis = AnalisisUsuario.objects.filter(user=user).first()
    if not analisis:
        errores.append("No se encontró análisis para el usuario")
        return errores, warnings
    
    # Verificar inconsistencias en rendimiento
    if analisis.rendimiento_general > 100:
        errores.append(f"Rendimiento general excede 100%: {analisis.rendimiento_general}%")
    
    if analisis.rendimiento_habitos > 100:
        errores.append(f"Rendimiento de hábitos excede 100%: {analisis.rendimiento_habitos}%")
    
    if analisis.rendimiento_tareas > 100:
        errores.append(f"Rendimiento de tareas excede 100%: {analisis.rendimiento_tareas}%")
    
    # Verificar hábitos vs registros
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    total_registros = RegistroHabito.objects.filter(habito__user=user).count()
    
    if analisis.total_habitos != habitos.count():
        warnings.append(f"Inconsistencia en conteo de hábitos: {analisis.total_habitos} vs {habitos.count()}")
    
    # Verificar rachas
    if analisis.racha_actual > analisis.mejor_racha:
        warnings.append("La racha actual es mayor que la mejor racha histórica")
    
    # Verificar días activo
    dias_activo_calculado = calcular_dias_activo(user)
    if analisis.dias_activo != dias_activo_calculado:
        warnings.append(f"Inconsistencia en días activo: {analisis.dias_activo} vs {dias_activo_calculado}")
    
    # Verificar registros con fechas futuras
    registros_futuros = RegistroHabito.objects.filter(
        habito__user=user,
        fecha__gt=today
    )
    
    if registros_futuros.exists():
        errores.append(f"Se encontraron {registros_futuros.count()} registros con fechas futuras")
    
    # Verificar registros duplicados
    registros_duplicados = RegistroHabito.objects.filter(
        habito__user=user
    ).values('habito', 'fecha').annotate(
        count=models.Count('id')
    ).filter(count__gt=1)
    
    if registros_duplicados.exists():
        errores.append(f"Se encontraron {registros_duplicados.count()} registros duplicados")
    
    return errores, warnings

@login_required
def reporte_errores_analisis(request):
    """Vista para mostrar errores detectados en el análisis"""
    user = request.user
    errores, warnings = detectar_errores_analisis(user)
    
    context = {
        'errores': errores,
        'warnings': warnings,
        'total_errores': len(errores),
        'total_warnings': len(warnings),
        'current_date': timezone.now().date()
    }
    
    return render(request, 'data_analytics/error.html', context)
