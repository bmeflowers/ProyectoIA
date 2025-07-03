from django import forms
from .models import Actividad, RegistroHabito

from django import forms
from .models import Actividad

from django import forms
from .models import Actividad

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['nombre', 'descripcion', 'tipo', 'fecha_limite', 'hora_habito']
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'placeholder': 'Ej: Leer un libro',
                    'id': 'id_nombre'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'placeholder': 'Ej: Leer 20 páginas del libro de historia',
                    'id': 'id_descripcion'
                }
            ),
            'tipo': forms.Select(
                attrs={
                    'id': 'id_tipo'
                }
            ),
            'fecha_limite': forms.DateInput(
                attrs={
                    'type': 'date',
                    'placeholder': 'Ej: 2025-07-05',
                    'id': 'id_fecha_limite'
                }
            ),
            'hora_habito': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'placeholder': 'Ej: 07:30',
                    'id': 'id_hora_habito'
                }
            ),
        }

class RegistroHabitoForm(forms.ModelForm):
    class Meta:
        model = RegistroHabito
        fields = ['estado']