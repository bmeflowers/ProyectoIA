from django import forms
from .models import Actividad, RegistroHabito

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['nombre', 'descripcion', 'tipo', 'fecha_limite', 'hora_habito']

        


class RegistroHabitoForm(forms.ModelForm):
    class Meta:
        model = RegistroHabito
        fields = ['estado']