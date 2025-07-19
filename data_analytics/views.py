import json
from django.shortcuts import render
from django.utils import timezone
from activities.models import Actividad, RegistroHabito
from django.db.models import Count, Q
from reminders.tasks import send_general_notification
from webpush.models import PushInformation


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

        progreso = int((total_completados / META_DIAS) * 100) if META_DIAS > 0 else 0
        if progreso > 100:
            progreso = 100

        labels.append(habito.nombre)
        data.append(progreso)

        stats.append({
            'nombre': habito.nombre,
            'total_completados': total_completados,
        })

        # Verifica si el usuario tiene suscripción push antes de enviar
        tiene_suscripcion = PushInformation.objects.filter(user=user).exists()

        if progreso < 50 and tiene_suscripcion:
            send_general_notification.apply(args=[
                user.id,
                f'¡Tu progreso en {habito.nombre} es menor al 50%! ¡Anímate!'
            ])
            
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
