from django import forms
from .models import Bitacora, Tutoria, Asistencia

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para input type="date" (formato: YYYY-MM-DD)
        if self.instance and self.instance.pk and self.instance.fecha_registro:
            self.initial['fecha_registro'] = self.instance.fecha_registro.strftime('%Y-%m-%d')

class TutoriaForm(forms.ModelForm):
    class Meta:
        model = Tutoria
        # No incluimos 'tutor' porque se asignará automático al usuario logueado
        fields = ['fecha', 'tema_tutoria', 'lugar', 'tipo_tutoria', 'clasificacion_tutoria']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tema_tutoria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'lugar': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_tutoria': forms.Select(attrs={'class': 'form-control'}),
            'clasificacion_tutoria': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para datetime-local (formato: YYYY-MM-DDTHH:MM)
        if self.instance and self.instance.pk and self.instance.fecha:
            self.initial['fecha'] = self.instance.fecha.strftime('%Y-%m-%dT%H:%M')