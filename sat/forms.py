from django import forms
from .models import Bitacora

class BitacoraForm(forms.ModelForm):
    class Meta:
        model = Bitacora
        # Solo pedimos estos dos campos.
        # El estudiante y la fecha se ponen automáticamente en el backend. (agregar fecha en el save() del view)

        fields = ['fecha_registro', 'observacion', 'alarma']
        
        # Aquí le ponemos "maquillaje" (clases de Bootstrap) para que se vea bonito
        widgets = {
            'fecha_registro': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe la situación del estudiante...'
            }),
            'alarma': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'fecha_registro': 'Fecha de la Observación',
            'observacion': 'Detalle de la Observación',
            'alarma': 'Tipo de Alarma (si aplica)',
        }