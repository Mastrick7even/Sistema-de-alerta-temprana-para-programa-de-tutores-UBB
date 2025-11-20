from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin # Obliga a estar logueado
from django.views.generic import ListView
from .models import Estudiante, Usuario

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
        

