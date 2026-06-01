from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Bitacora, ComentarioBitacora, Tutoria, Asistencia, Usuario, Carrera, Rol,
    TipoAlarma, TipoTutoria, ClasificacionTutoria, TipoDesercion, Estado
)


# ─────────────────────────────────────────────────────────────────
# FORMS ADMINISTRATIVOS (solo superuser)
# ─────────────────────────────────────────────────────────────────

W = 'form-control'  # shorthand para widgets

class UsuarioAdminForm(forms.Form):
    """
    Formulario para Crear / Editar un usuario SAT (sat.Usuario + auth.User).
    Opera sobre ambos modelos de forma atómica en la vista.
    """
    nombre    = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': W}))
    apellido  = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': W}))
    rut       = forms.CharField(max_length=12,  widget=forms.TextInput(attrs={'class': W, 'placeholder': '12345678-9'}))
    email     = forms.EmailField(widget=forms.EmailInput(attrs={'class': W}))
    username  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': W}))
    rol       = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.Select(attrs={'class': W}),
        empty_label='-- Seleccione un rol --'
    )
    carrera   = forms.ModelChoiceField(
        queryset=Carrera.objects.all(),
        widget=forms.Select(attrs={'class': W}),
        required=False,
        empty_label='-- Sin carrera asignada --'
    )
    password  = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': W, 'placeholder': 'Dejar en blanco para no cambiar'}),
        label='Contraseña',
        help_text='Mínimo 8 caracteres. Dejar vacío al editar para mantener la actual.'
    )

    def clean_rut(self):
        return self.cleaned_data['rut'].strip()

    def clean_password(self):
        pw = self.cleaned_data.get('password', '').strip()
        if pw and len(pw) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return pw


class CarreraAdminForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['nombre', 'encargado']
        widgets = {
            'nombre':    forms.TextInput(attrs={'class': W}),
            'encargado': forms.Select(attrs={'class': W}),
        }
        labels = {
            'nombre':    'Nombre de la carrera',
            'encargado': 'Encargado de Carrera',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar usuarios con rol EC en el select de encargado
        from .models import Rol
        try:
            rol_ec = Rol.objects.get(nombre='Encargado de Carrera')
            self.fields['encargado'].queryset = Usuario.objects.filter(rol=rol_ec)
        except Rol.DoesNotExist:
            self.fields['encargado'].queryset = Usuario.objects.none()


class TipoAlarmaForm(forms.ModelForm):
    class Meta:
        model = TipoAlarma
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': W, 'placeholder': 'Nombre del tipo de alarma'})}


class TipoTutoriaForm(forms.ModelForm):
    class Meta:
        model = TipoTutoria
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': W, 'placeholder': 'Nombre del tipo de tutoría'})}


class ClasificacionTutoriaForm(forms.ModelForm):
    class Meta:
        model = ClasificacionTutoria
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': W, 'placeholder': 'Nombre de la clasificación'})}


class TipoDesercionForm(forms.ModelForm):
    class Meta:
        model = TipoDesercion
        fields = ['causa']
        widgets = {'causa': forms.TextInput(attrs={'class': W, 'placeholder': 'Causa de deserción'})}


class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': W, 'placeholder': 'Nombre del estado'})}



class BitacoraForm(forms.ModelForm):
    class Meta:
        model = Bitacora
        # Solo pedimos estos dos campos.
        # El estudiante y la fecha se ponen automáticamente en el backend. (agregar fecha en el save() del view)

        fields = ['fecha_registro', 'estado_atencion', 'observacion', 'alarma']
        
        # Aquí le ponemos "maquillaje" (clases de Bootstrap) para que se vea bonito
        widgets = {
            'fecha_registro': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'estado_atencion': forms.Select(attrs={
                'class': 'form-control'
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
            'estado_atencion': 'Estado de Atención',
            'observacion': 'Detalle de la Observación',
            'alarma': 'Tipo de Alarma (si aplica)',
        }

class ComentarioBitacoraForm(forms.ModelForm):
    class Meta:
        model = ComentarioBitacora
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Agregar actualización o sub-observación...'
            }),
        }
        labels = {
            'texto': '',
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

import os

class CargaMasivaForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo de Carga Masiva',
        help_text='Selecciona un archivo con extensión .csv o .xlsx',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            ext = os.path.splitext(archivo.name)[1].lower()
            if ext not in ['.csv', '.xlsx']:
                raise forms.ValidationError('Formato no soportado. Sube un archivo .csv o .xlsx')
        return archivo