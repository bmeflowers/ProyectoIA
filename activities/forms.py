from django import forms
from .models import Actividad, RegistroHabito

class ActividadForm(forms.ModelForm):
    # Campo personalizado para seleccionar tipo de meta
    tipo_meta = forms.ChoiceField(
        choices=[
            ('dias', 'Días'),
            ('meses', 'Meses'),
        ],
        initial='dias',
        label='Tipo de Meta',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_tipo_meta'
        })
    )
    
    # Campo para el valor de la meta
    valor_meta = forms.IntegerField(
        min_value=1,
        max_value=3650,  # Máximo 10 años
        initial=30,
        label='Valor de la Meta',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_valor_meta',
            'placeholder': 'Ej: 30 días o 3 meses'
        })
    )
    
    class Meta:
        model = Actividad
        fields = ['icono', 'nombre', 'descripcion', 'tipo', 'fecha_limite', 'hora_habito', 'meta_dias']
        widgets = {
            'icono': forms.TextInput(attrs={
                'placeholder': 'Ej: 📚, 🏃‍♂️, ✍️',
                'id': 'id_icono',
                'class': 'form-control'
            }),
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej: Leer un libro', 
                'id': 'id_nombre',
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Ej: Leer 20 páginas', 
                'id': 'id_descripcion',
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'id': 'id_tipo',
                'class': 'form-control'
            }),
            'fecha_limite': forms.DateInput(attrs={
                'type': 'date', 
                'id': 'id_fecha_limite',
                'class': 'form-control'
            }),
            'hora_habito': forms.TimeInput(attrs={
                'type': 'time', 
                'id': 'id_hora_habito',
                'class': 'form-control'
            }),
            'meta_dias': forms.HiddenInput(),  # Campo oculto que se calculará automáticamente
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es una instancia existente, establecer los valores iniciales
        if self.instance and self.instance.pk:
            if self.instance.meta_dias:
                if self.instance.meta_dias >= 365:
                    # Si es más de un año, mostrar en meses
                    meses = self.instance.meta_dias // 30
                    self.fields['tipo_meta'].initial = 'meses'
                    self.fields['valor_meta'].initial = meses
                else:
                    # Si es menos de un año, mostrar en días
                    self.fields['tipo_meta'].initial = 'dias'
                    self.fields['valor_meta'].initial = self.instance.meta_dias
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_meta = cleaned_data.get('tipo_meta')
        valor_meta = cleaned_data.get('valor_meta')
        
        if tipo_meta and valor_meta:
            # Convertir a días según el tipo de meta
            if tipo_meta == 'meses':
                meta_dias = valor_meta * 30  # Aproximadamente 30 días por mes
            else:
                meta_dias = valor_meta
            
            cleaned_data['meta_dias'] = meta_dias
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asegurar que meta_dias se establezca correctamente
        if not instance.meta_dias:
            tipo_meta = self.cleaned_data.get('tipo_meta')
            valor_meta = self.cleaned_data.get('valor_meta')
            
            if tipo_meta and valor_meta:
                if tipo_meta == 'meses':
                    instance.meta_dias = valor_meta * 30
                else:
                    instance.meta_dias = valor_meta
        
        if commit:
            instance.save()
        return instance

class RegistroHabitoForm(forms.ModelForm):
    class Meta:
        model = RegistroHabito
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-control'
            })
        }