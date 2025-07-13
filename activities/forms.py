from django import forms
from .models import Actividad, RegistroHabito

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['icono', 'nombre', 'descripcion', 'tipo', 'fecha_limite', 'hora_habito']
        widgets = {
            'icono': forms.TextInput(attrs={
                'placeholder': 'Ej: 📚, 🏃‍♂️, ✍️',
                'id': 'id_icono'
            }),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Leer un libro', 'id': 'id_nombre'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Ej: Leer 20 páginas', 'id': 'id_descripcion'}),
            'tipo': forms.Select(attrs={'id': 'id_tipo'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'id': 'id_fecha_limite'}),
            'hora_habito': forms.TimeInput(attrs={'type': 'time', 'id': 'id_hora_habito'}),
        }

class RegistroHabitoForm(forms.ModelForm):
    class Meta:
        model = RegistroHabito
        fields = ['estado']