from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin # Obliga a estar logueado
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Estudiante, Usuario, Bitacora
from django.shortcuts import get_object_or_404
from .forms import BitacoraForm
from django.urls import reverse_lazy

class EstudianteListView(LoginRequiredMixin, ListView):
    model = Estudiante
    template_name = 'sat/estudiante_list.html'  # Dónde buscará el HTML
    context_object_name = 'estudiantes'         # Cómo llamarás a la lista en el HTML
    
    # Ordenar por apellido
    def get_queryset(self):

        # 1. Obtenemos el usuario logeado en el sistema
        django_user = self.request.user

        # 2. Si es un superusuario, que vea todo
        if django_user.is_superuser:
            return Estudiante.objects.all().order_by('apellido')
        
        # 3. Buscamos el perfil en TU tabla 'Usuario' usando el email
        try:
            perfil_tutor = Usuario.objects.get(email=django_user.email)
            # 4. Filtramos: Solo estudiantes donde tutor_asignado sea este perfil
            return Estudiante.objects.filter(tutor_asignado=perfil_tutor).order_by('apellido')
        except Usuario.DoesNotExist:
            # Si el usuario no existe en tu tabla SAT, no ve nada
            return Estudiante.objects.none
        
class EstudianteDetailView(LoginRequiredMixin, DetailView):
    model = Estudiante
    template_name = 'sat/estudiante_detail.html'
    context_object_name = 'estudiante'

    def get_queryset(self):

        django_user = self.request.user

        if django_user.is_superuser:
            return Estudiante.objects.all()
        
        try:
            perfil_tutor = Usuario.objects.get(email=django_user.email)
            return Estudiante.objects.filter(tutor_asignado=perfil_tutor)
        except Usuario.DoesNotExist:
            return Estudiante.objects.none

    def get_context_data(self, **kwargs): # Este método sirve para enviar datos EXTRA al template. (aquí enviaremos la bitácora del tutorado)
        context = super().get_context_data(**kwargs) 
        estudiante_actual = self.object # 'self.object' es el estudiante que Django ya encontró por nosotros
        context['bitacoras'] = estudiante_actual.bitacora_set.all().order_by('-fecha_registro')
        return context
    
class BitacoraCreateView(LoginRequiredMixin, CreateView):
    model = Bitacora
    form_class = BitacoraForm
    template_name = 'sat/bitacora_form.html'

    def setup(self, request, *args, **kwargs):
        """ 
        Este método se ejecuta al principio. Lo usamos para buscar al estudiante
        antes de cargar nada, así lo tenemos disponible siempre.
        """
        super().setup(request, *args, **kwargs)
        # Buscamos al estudiante por la PK que viene en la URL
        self.estudiante = get_object_or_404(Estudiante, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        """ Enviamos al estudiante al HTML para poner su nombre en el título """
        context = super().get_context_data(**kwargs)
        context['estudiante'] = self.estudiante
        return context

    def form_valid(self, form):
        """
        Aquí ocurre la magia. Antes de guardar el formulario,
        le asignamos el estudiante automáticamente.
        """
        form.instance.estudiante = self.estudiante
        return super().form_valid(form)

    def get_success_url(self):
        """ Una vez guardado, volvemos al perfil del estudiante """
        return reverse_lazy('estudiante-detail', kwargs={'pk': self.estudiante.pk})

# === VISTA PARA EDITAR ===
class BitacoraUpdateView(LoginRequiredMixin, UpdateView):
    model = Bitacora
    form_class = BitacoraForm  # <--- IMPORTANTE: Usamos tu form con calendario
    template_name = 'sat/bitacora_form.html' # Reutilizamos el mismo HTML

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasamos el estudiante para que el botón "Cancelar" sepa dónde volver
        context['estudiante'] = self.object.estudiante
        context['titulo'] = 'Editar Observación' # Para cambiar el título en el HTML
        return context

    def get_success_url(self):
        # Al guardar, volvemos al perfil del estudiante
        return reverse_lazy('estudiante-detail', kwargs={'pk': self.object.estudiante.pk})

# === VISTA PARA BORRAR ===
class BitacoraDeleteView(LoginRequiredMixin, DeleteView):
    model = Bitacora
    template_name = 'sat/bitacora_confirm_delete.html' # HTML de confirmación

    def get_success_url(self):
        # Al borrar, recarga la misma página del perfil
        return reverse_lazy('estudiante-detail', kwargs={'pk': self.object.estudiante.pk})

