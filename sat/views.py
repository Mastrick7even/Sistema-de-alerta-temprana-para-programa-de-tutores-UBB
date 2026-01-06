from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin # Obliga a estar logueado
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
import os
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Estudiante, Usuario, Bitacora, Estado, Carrera, TipoAlarma, Tutoria, Asistencia, Notificacion
from .forms import BitacoraForm, TutoriaForm

class EstudianteListView(LoginRequiredMixin, ListView):
    model = Estudiante
    template_name = 'sat/estudiante_list.html'  # Dónde buscará el HTML
    context_object_name = 'estudiantes'         # Cómo llamarás a la lista en el HTML
    paginate_by = 10
    
    # Ordenar por apellido
    def get_queryset(self):
        # 1. Queryset Base: ¿Quién soy y a quién puedo ver?
        queryset = super().get_queryset()
        user = self.request.user
        
        try:
            perfil = Usuario.objects.get(email=user.email)
            if perfil.rol.nombre == 'Tutor':
                # El Tutor solo ve sus asignados
                queryset = queryset.filter(tutor_asignado=perfil)
            # El Encargado ve todo (o podrías filtrar por su carrera si quisieras)
        except Usuario.DoesNotExist:
            if not user.is_superuser:
                return Estudiante.objects.none()

        # 2. FILTROS INTELIGENTES (Aquí ocurre la magia)
        
        # A. Búsqueda por Texto (Nombre, Apellido o RUT)
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) | 
                Q(apellido__icontains=search_query) |
                Q(rut__icontains=search_query)
            )

        # B. Filtro por Estado de Riesgo
        estado_filter = self.request.GET.get('estado')
        if estado_filter:
            queryset = queryset.filter(estado_actual__id_estado=estado_filter)

        # C. Filtro por Carrera (Solo útil para Encargados o Admins)
        carrera_filter = self.request.GET.get('carrera')
        if carrera_filter:
            queryset = queryset.filter(carrera__id_carrera=carrera_filter)

        return queryset.order_by('-id_estudiante')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasamos las listas para llenar los <select> del HTML
        context['lista_carreras'] = Carrera.objects.all()
        context['lista_estados'] = Estado.objects.all()
        return context
        
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
        try:
            perfil = Usuario.objects.get(email=self.request.user.email)
            form.instance.autor = perfil
        except Usuario.DoesNotExist:
            pass
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

# === VISTA PARA EL DASHBOARD ===
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'sat/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        django_user = self.request.user
        
        es_tutor = False
        es_encargado = False
        
        if not django_user.is_superuser:
            try:
                perfil = Usuario.objects.get(email=django_user.email)
                if perfil.rol.nombre == 'Tutor':
                    es_tutor = True
                elif perfil.rol.nombre == 'Encargado de Carrera': # Asegúrate del nombre exacto en BD
                    es_encargado = True
            except Usuario.DoesNotExist:
                pass # O manejar error
        
        context['es_tutor'] = es_tutor
        context['es_encargado'] = es_encargado

        # 1. Determinar qué estudiantes ver (Lógica de Permisos)
        if django_user.is_superuser:
            mis_estudiantes = Estudiante.objects.all()
        else:
            try:
                # Buscamos al usuario SAT por email
                perfil_usuario = Usuario.objects.get(email=django_user.email)
                
                # Si es Tutor, filtramos. Si es Encargado, ve todo.
                if perfil_usuario.rol.nombre == 'Tutor':
                    mis_estudiantes = Estudiante.objects.filter(tutor_asignado=perfil_usuario)
                else:
                    # Asumimos que es Encargado (ve todo)
                    # O podrías filtrar por carrera si el encargado tiene una asignada
                    mis_estudiantes = Estudiante.objects.all()
            except Usuario.DoesNotExist:
                mis_estudiantes = Estudiante.objects.none()

        # 2. Calcular KPIs (Indicadores)
        total_estudiantes = mis_estudiantes.count()
        
        # Contamos según el nombre del Estado (Ajusta los nombres a lo que pusiste en tu BD)
        # Usamos __icontains para que busque "Alto" aunque sea "Riesgo Alto"
        riesgo_alto = mis_estudiantes.filter(estado_actual__nombre__icontains='Alto').count()
        riesgo_medio = mis_estudiantes.filter(estado_actual__nombre__icontains='Medio').count()
        riesgo_bajo = mis_estudiantes.filter(estado_actual__nombre__icontains='Bajo').count()

        # 3. Bitácoras recientes (de MIS estudiantes)
        ultimas_bitacoras = Bitacora.objects.filter(estudiante__in=mis_estudiantes)
        
        # A. Filtro por Carrera
        carrera_filter = self.request.GET.get('carrera_dashboard')
        if carrera_filter:
            ultimas_bitacoras = ultimas_bitacoras.filter(
                estudiante__carrera__id_carrera=carrera_filter
            )
        
        # B. Filtro por Rango de Fechas
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_desde:
            ultimas_bitacoras = ultimas_bitacoras.filter(
                fecha_registro__date__gte=fecha_desde
            )
        if fecha_hasta:
            ultimas_bitacoras = ultimas_bitacoras.filter(
                fecha_registro__date__lte=fecha_hasta
            )
        
        # C. Filtro por Tipo de Alerta
        alerta_filter = self.request.GET.get('tipo_alerta')
        if alerta_filter:
            ultimas_bitacoras = ultimas_bitacoras.filter(
                alarma__tipo_alarma__id_tipo=alerta_filter
            )
        
        # Limitar resultados: 5 si no hay filtros, todas si hay filtros
        if not any([carrera_filter, fecha_desde, fecha_hasta, alerta_filter]):
            ultimas_bitacoras = ultimas_bitacoras.order_by('-fecha_registro')[:5]
        else:
            ultimas_bitacoras = ultimas_bitacoras.order_by('-fecha_registro')

        # 4. Inyectar datos al HTML
        context['kpi_total'] = total_estudiantes
        context['kpi_alto'] = riesgo_alto
        context['kpi_medio'] = riesgo_medio
        context['kpi_bajo'] = riesgo_bajo
        context['ultimas_bitacoras'] = ultimas_bitacoras
        
        # Listas para los filtros del dashboard
        context['lista_carreras_dashboard'] = Carrera.objects.all()
        context['lista_alertas'] = TipoAlarma.objects.all()

        # Datos para el gráfico [Alto, Medio, Bajo, Sin Riesgo]
        # Asegúrate que el orden coincida con los colores que pondremos en el HTML
        data_grafico = [riesgo_alto, riesgo_medio, riesgo_bajo] 
        
        context['data_grafico'] = data_grafico

        # Calcular estudiantes por año de ingreso
        datos_ingreso = mis_estudiantes.values('anio_ingreso').annotate(total=Count('id_estudiante')).order_by('anio_ingreso')

        # Preparamos dos listas para Chart.js
        labels_ingreso = [str(d['anio_ingreso']) for d in datos_ingreso]
        data_ingreso = [d['total'] for d in datos_ingreso]

        context['labels_ingreso'] = labels_ingreso
        context['data_ingreso'] = data_ingreso
        
        return context

# Reporte PDF
class ReporteEstudiantePDF(LoginRequiredMixin, DetailView):
    model = Estudiante
    
    def get(self, request, *args, **kwargs):
        estudiante = self.get_object()
        
        # Obtenemos las bitácoras ordenadas
        bitacoras = Bitacora.objects.filter(estudiante=estudiante).order_by('-fecha_registro')
        
        # Contexto para el template
        context = {
            'estudiante': estudiante,
            'bitacoras': bitacoras,
            'usuario_generador': request.user,
        }
        
        # 1. Renderizar HTML a string
        html_string = render_to_string('sat/reporte_pdf.html', context)
        
        # 2. Intentar generar PDF con WeasyPrint (mejor calidad, requiere GTK+ en Windows)
        try:
            from weasyprint import HTML, CSS
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
            pdf_file = html.write_pdf()
            
        except (ImportError, OSError) as e:
            # Fallback: usar xhtml2pdf (funciona en Windows sin dependencias externas)
            try:
                from xhtml2pdf import pisa
                from io import BytesIO
                
                pdf_buffer = BytesIO()
                pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
                
                if pisa_status.err:
                    return HttpResponse(
                        f"Error al generar PDF: {pisa_status.err}",
                        status=500
                    )
                
                pdf_file = pdf_buffer.getvalue()
                pdf_buffer.close()
                
            except ImportError:
                return HttpResponse(
                    "Error: No hay librerías PDF instaladas. "
                    "Instala 'weasyprint' (con GTK+) o 'xhtml2pdf' (pip install xhtml2pdf).",
                    status=500
                )
        
        # 3. Respuesta HTTP con el PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f"Ficha_{estudiante.rut}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    
# 1. LISTAR MIS TUTORÍAS
class MisTutoriasView(LoginRequiredMixin, ListView):
    model = Tutoria
    template_name = 'sat/tutorias_list.html'
    context_object_name = 'tutorias'

    def get_queryset(self):
        # Solo veo las tutorías que YO creé
        try:
            perfil = Usuario.objects.get(email=self.request.user.email)
            return Tutoria.objects.filter(tutor=perfil).order_by('-fecha')
        except Usuario.DoesNotExist:
            return Tutoria.objects.none()

# 2. CREAR NUEVA TUTORÍA
class TutoriaCreateView(LoginRequiredMixin, CreateView):
    model = Tutoria
    form_class = TutoriaForm
    template_name = 'sat/tutoria_form.html'
    success_url = '/tutorias/' # Ajusta a tu URL de lista

    def form_valid(self, form):
        # Asignar automáticamente el tutor actual
        perfil = Usuario.objects.get(email=self.request.user.email)
        form.instance.tutor = perfil
        return super().form_valid(form)

# 3. EDITAR TUTORÍA
class TutoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Tutoria
    form_class = TutoriaForm
    template_name = 'sat/tutoria_form.html'
    success_url = '/tutorias/'
    
    def get_queryset(self):
        # Solo permitir editar las tutorías propias
        perfil = Usuario.objects.get(email=self.request.user.email)
        return Tutoria.objects.filter(tutor=perfil)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Tutoría'
        return context

# 4. ELIMINAR TUTORÍA
class TutoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Tutoria
    success_url = '/tutorias/'
    
    def get_queryset(self):
        # Solo permitir eliminar las tutorías propias
        perfil = Usuario.objects.get(email=self.request.user.email)
        return Tutoria.objects.filter(tutor=perfil)

# 3. TOMAR ASISTENCIA (La lógica interesante)
def tomar_asistencia(request, pk):
    # pk es el ID de la tutoría
    tutoria = get_object_or_404(Tutoria, pk=pk)
    
    # Obtenemos SOLO los estudiantes asignados a este tutor
    mis_estudiantes = Estudiante.objects.filter(tutor_asignado=tutoria.tutor)

    if request.method == 'POST':
        # Procesar el formulario manual
        for estudiante in mis_estudiantes:
            # En el HTML pondremos inputs con nombre "asistencia_IDESTUDIANTE"
            estado = request.POST.get(f'asistencia_{estudiante.id_estudiante}')
            
            # Guardamos o actualizamos
            # update_or_create busca por (tutoria, estudiante) y actualiza el estado
            Asistencia.objects.update_or_create(
                tutoria=tutoria,
                estudiante=estudiante,
                defaults={'estado_asistencia': estado}
            )
        
        messages.success(request, 'Asistencia registrada correctamente.')
        return redirect('mis-tutorias') # Volver al listado

    # Si es GET, preparamos datos previos si existen
    asistencias_previas = Asistencia.objects.filter(tutoria=tutoria)
    # Creamos un diccionario { id_estudiante: estado } para pintar el HTML
    mapa_asistencia = {a.estudiante.id_estudiante: a.estado_asistencia for a in asistencias_previas}

    return render(request, 'sat/tomar_asistencia.html', {
        'tutoria': tutoria,
        'estudiantes': mis_estudiantes,
        'mapa_asistencia': mapa_asistencia
    })

@login_required
def leer_notificacion(request, pk):
    noti = get_object_or_404(Notificacion, pk=pk)
    
    # Seguridad: Solo el dueño puede leerla
    try:
        perfil_usuario = Usuario.objects.get(email=request.user.email)
        if noti.destinatario == perfil_usuario:
            noti.leida = True
            noti.save()
    except Usuario.DoesNotExist:
        pass  # Si no tiene perfil SAT, no puede marcar como leída
        
    # Redirigir al estudiante relacionado si existe
    if noti.estudiante_relacionado:
        return redirect('estudiante-detail', pk=noti.estudiante_relacionado.id_estudiante)
    
    # Si no, al dashboard
    return redirect('home')

# views.py
@login_required
def todas_notificaciones(request):
    try:
        from django.core.paginator import Paginator
        
        perfil = Usuario.objects.get(email=request.user.email)
        notificaciones_list = Notificacion.objects.filter(destinatario=perfil).order_by('-fecha_creacion')
        
        # Paginación: 10 notificaciones por página
        paginator = Paginator(notificaciones_list, 10)
        page_number = request.GET.get('page')
        notificaciones = paginator.get_page(page_number)
        
        return render(request, 'sat/notificaciones.html', {
            'notificaciones': notificaciones,
            'total_notificaciones': notificaciones_list.count()
        })
    except Usuario.DoesNotExist:
        return redirect('home')

@login_required
def marcar_notificaciones_leidas(request):
    """Marca múltiples notificaciones como leídas"""
    if request.method == 'POST':
        notificacion_ids = request.POST.getlist('notificaciones[]')
        try:
            perfil = Usuario.objects.get(email=request.user.email)
            Notificacion.objects.filter(
                id__in=notificacion_ids,
                destinatario=perfil
            ).update(leida=True)
            messages.success(request, f'{len(notificacion_ids)} notificación(es) marcada(s) como leída(s).')
        except Usuario.DoesNotExist:
            messages.error(request, 'Error al procesar la solicitud.')
    return redirect('todas-notificaciones')

@login_required
def eliminar_notificaciones(request):
    """Elimina múltiples notificaciones"""
    if request.method == 'POST':
        notificacion_ids = request.POST.getlist('notificaciones[]')
        try:
            perfil = Usuario.objects.get(email=request.user.email)
            count = Notificacion.objects.filter(
                id__in=notificacion_ids,
                destinatario=perfil
            ).delete()[0]
            messages.success(request, f'{count} notificación(es) eliminada(s).')
        except Usuario.DoesNotExist:
            messages.error(request, 'Error al procesar la solicitud.')
    return redirect('todas-notificaciones')
