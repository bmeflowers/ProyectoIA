from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Actividad, RegistroHabito
from .forms import ActividadForm, RegistroHabitoForm
from datetime import date

@login_required
def activities(request):
    actividades = Actividad.objects.filter(user=request.user).order_by('-fecha_creacion')
    return render(request, 'activities/activities.html', {'actividades': actividades})

@login_required
def agregar_actividad(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.user = request.user
            actividad.estado = 'pendiente'  # ✅ Aquí le damos un valor por defecto

            if actividad.tipo == 'habito':
                actividad.dias_semana = request.POST.getlist('dias_semana')

            actividad.save()
            return redirect('activities:activities')
        else:
            print("❌ Errores en el formulario:", form.errors)
    else:
        form = ActividadForm()
    return render(request, 'activities/agregarActividad.html', {'form': form})


@login_required
def eliminar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, user=request.user)
    actividad.delete()
    return redirect('activities:activities')

@login_required
def cambiar_estado(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, user=request.user)
    if actividad.tipo == 'tarea':
        actividad.estado = 'completado' if actividad.estado == 'pendiente' else 'pendiente'
        actividad.save()
    return redirect('activities:activities')

@login_required
def registrar_habito(request, pk):
    habito = get_object_or_404(Actividad, pk=pk, user=request.user, tipo='habito')
    hoy = date.today()
    registro, creado = RegistroHabito.objects.get_or_create(habito=habito, fecha=hoy)

    if request.method == 'POST':
        form = RegistroHabitoForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            return redirect('activities:activities')
    else:
        form = RegistroHabitoForm(instance=registro)

    return render(request, 'activities/registrarHabito.html', {
        'habito': habito,
        'form': form,
        'fecha': hoy,
    })
