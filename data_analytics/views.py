import json
from django.shortcuts import render
from datetime import date

def dashboard(request):
    context = {
        'current_date': date.today().strftime('%d %B %Y'),
        # Datos fijos para dashboard normal
        'tejer': 20,
        'correr': 20,
        'leer': 20,
        'progreso_tejer': 75,
        'progreso_correr': 50,
        'progreso_leer': 90,
    }
    return render(request, 'data_analytics/dashboard.html', context)

def dashboard_advanced(request):
    # Datos fijos para el dashboard avanzado
    context = {
        'current_date': date.today().strftime('%d %B %Y'),
        'total_usuarios': 120,
        'habitos_registrados': 42,
        'tareas_completadas': 350,
        'promedio_actividad': 89,
    }
    return render(request, 'data_analytics/dashboard_advanced.html', context)
