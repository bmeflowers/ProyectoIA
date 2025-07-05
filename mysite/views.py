from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from activities.models import Actividad
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .chatbot import obtener_respuesta

@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body)
        mensaje = data.get("mensaje", "").strip()
        if not mensaje:
            return JsonResponse({"error": "No se envió ningún mensaje."}, status=400)

        respuesta = obtener_respuesta(mensaje)
        return JsonResponse({"respuesta": respuesta})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def dashboard(request):
    today = timezone.now().date()
    actividades = Actividad.objects.filter(user=request.user).order_by('-fecha_creacion')
    
    habitos = actividades.filter(tipo='habito')
    tareas = actividades.filter(tipo='tarea')
    return render(request, 'dashboard.html', {
        'today': today,
        'habitos': habitos,
        'tareas': tareas,
    })

