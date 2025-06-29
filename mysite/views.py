from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from activities.models import Actividad

@login_required 
def dashboard(request):
    today = timezone.now()
    habitos = Actividad.objects.filter(user=request.user, tipo='habito')
    return render(request, 'dashboard.html', {
        'today': today,
        'habitos': habitos,
    })
