import json
from django.shortcuts import render
from django.utils import timezone
from activities.models import Actividad, RegistroHabito
from django.db.models import Count, Q
from reminders.tasks import send_general_notification

def dashboard(request):
    user = request.user
    current_date = timezone.localdate()

    habitos = Actividad.objects.filter(user=user, tipo='habito')

    labels = []
    data = []
    stats = []

    META_DIAS = 25

    for habito in habitos:
        total_completados = habito.registros.filter(estado='completado').count()

        # Calcular progreso en base a la meta fija de 150 días
        progreso = int((total_completados / META_DIAS) * 100) if META_DIAS > 0 else 0
        if progreso > 100:
            progreso = 100

        labels.append(habito.nombre)
        data.append(progreso)

        stats.append({
            'nombre': habito.nombre,
            'total_completados': total_completados,
        })

        if progreso < 50:  # Ejemplo: Si el progreso es bajo, envía una notificación
            send_general_notification.delay(request.user.id, f'¡Tu progreso en {habito.nombre} es menor al 50%! ¡Anímate!')

    context = {
        'current_date': current_date,
        'labels_json': json.dumps(labels),
        'data_json': json.dumps(data),
        'stats': stats,
        'user': user,
    }
    return render(request, 'data_analytics/dashboard.html', context)

def dashboard_advanced(request):
    context = {
        'current_date': timezone.localdate(),
        'total_usuarios': 120,
        'habitos_registrados': 42,
        'tareas_completadas': 350,
        'promedio_actividad': 89,
    }
    return render(request, 'data_analytics/dashboard_advanced.html', context)
