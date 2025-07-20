from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Actividad, RegistroHabito
from .forms import ActividadForm, RegistroHabitoForm
from django.utils import timezone
from datetime import date

@login_required
def activities(request):
    today = timezone.now().date()
    actividades = Actividad.objects.filter(user=request.user).order_by('-fecha_creacion')
    habitos = actividades.filter(tipo='habito')
    tareas = actividades.filter(tipo='tarea')

    # Enriquecer los hábitos con datos adicionales
    for habito in habitos:
        habito.total_registros = habito.registros.count()  # Usa related_name 'registros'
        habito.registrado_hoy = habito.registros.filter(fecha=today).exists()

    return render(request, 'activities/activities.html', {
        'today': today,
        'habitos': habitos,
        'tareas': tareas
    })

@login_required
def agregar_actividad(request):
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    emojis = ['🚴🏻','💪🏻','👩‍💻','🏊🏻','🍳','☕','🏀','🎨','🎮','🧶','📚','🎻','🏃🏻‍♂️', '🚶🏻‍♀️','🧹🧺'
              '💎', '🧘🏻‍♂️', '📖']

    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.user = request.user
            actividad.estado = 'pendiente'
            if actividad.tipo == 'habito':
                actividad.dias_semana = request.POST.getlist('dias_semana')
            else:
                actividad.dias_semana = None
            actividad.save()
            return redirect('activities:activities')
        else:
            print("❌ Errores en el formulario:", form.errors)
    else:
        form = ActividadForm()

    context = {
        'form': form,
        'dias_semana': dias_semana,
        'emojis': emojis,
    }
    return render(request, 'activities/agregarActividad.html', context)


@login_required
def eliminar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, user=request.user)
    actividad.delete()
    return redirect('activities:activities')

@login_required
def cambiar_estado(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, user=request.user)
    if actividad.tipo == 'tarea':
        actividad.estado = 'Registrar' if actividad.estado == 'completado' else 'completado'
        actividad.save()
    return redirect('activities:activities')

@login_required
def registrar_habito(request, pk):
    habito = get_object_or_404(Actividad, pk=pk, user=request.user, tipo='habito')
    hoy = date.today()
    
    # Intenta obtener un registro existente para hoy
    try:
        registro = RegistroHabito.objects.get(habito=habito, fecha=hoy)
        registrado_hoy = True
    except RegistroHabito.DoesNotExist:
        registro = None
        registrado_hoy = False

    if request.method == 'POST':
        form = RegistroHabitoForm(request.POST, instance=registro)
        if form.is_valid():
            nuevo_registro = form.save(commit=False)
            nuevo_registro.habito = habito
            nuevo_registro.fecha = hoy
            nuevo_registro.estado = 'completado'
            nuevo_registro.save()
            return redirect('activities:activities')
    else:
        form = RegistroHabitoForm(instance=registro)
    
    return render(request, 'activities/registrarHabito.html', {
        'habito': habito,
        'form': form,
        'fecha': hoy,
        'registrado_hoy': registrado_hoy
    })
    