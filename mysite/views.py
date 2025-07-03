from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from activities.models import Actividad

@login_required
def dashboard(request):
    today = timezone.now().date()
    actividades = Actividad.objects.filter(user=request.user).order_by('-fecha_creacion')
    
    habitos = actividades.filter(tipo='habito')
    tareas = actividades.filter(tipo='tarea')  # 👈 Asegúrate de que esto exista

    return render(request, 'dashboard.html', {
        'today': today,
        'habitos': habitos,
        'tareas': tareas,  # 👈 Y que estés pasando esto
    })

