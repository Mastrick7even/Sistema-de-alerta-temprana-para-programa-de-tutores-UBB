from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.db.models import Count, Q, Case, When, IntegerField
from django.db import transaction
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib import messages
from django.views import View
import os, secrets, string
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import (
    Estudiante, Usuario, Bitacora, Estado, Carrera, TipoAlarma, Tutoria,
    Asistencia, Notificacion, HistorialRiesgo, Rol, TipoTutoria,
    ClasificacionTutoria, TipoDesercion
)
from .forms import (
    BitacoraForm, TutoriaForm,
    UsuarioAdminForm, CarreraAdminForm,
    TipoAlarmaForm, TipoTutoriaForm, ClasificacionTutoriaForm,
    TipoDesercionForm, EstadoForm
)

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
            elif perfil.rol.nombre == 'Encargado de Carrera':
                # El EC solo ve estudiantes de sus carreras asignadas
                carreras_ec = Carrera.objects.filter(encargado=perfil)
                queryset = queryset.filter(carrera__in=carreras_ec)
        except Usuario.DoesNotExist:
            if not user.is_superuser:
                return Estudiante.objects.none()

        # 2. FILTROS INTELIGENTES (Conectados a la IA)
        
        # A. Búsqueda por Texto (Nombre, Apellido o RUT)
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) | 
                Q(apellido__icontains=search_query) |
                Q(rut__icontains=search_query)
            )

        # B. NUEVO Filtro por Nivel de Riesgo IA
        riesgo_filter = self.request.GET.get('riesgo_ia')
        # Usamos != '' y is not None porque "0" es un valor válido (Sin Riesgo)
        if riesgo_filter != '' and riesgo_filter is not None:
            queryset = queryset.filter(nivel_riesgo_ia=int(riesgo_filter))

        # C. Filtro por Carrera
        carrera_filter = self.request.GET.get('carrera')
        if carrera_filter:
            queryset = queryset.filter(carrera__id_carrera=carrera_filter)

        return queryset.order_by('-id_estudiante')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar carreras del dropdown según el rol del usuario
        user = self.request.user
        if user.is_superuser:
            context['lista_carreras'] = Carrera.objects.all()
        else:
            try:
                perfil = Usuario.objects.get(email=user.email)
                if perfil.rol.nombre == 'Tutor':
                    # El tutor solo ve la carrera de sus alumnos asignados
                    ids = Estudiante.objects.filter(tutor_asignado=perfil).values_list('carrera', flat=True).distinct()
                    context['lista_carreras'] = Carrera.objects.filter(id_carrera__in=ids)
                elif perfil.rol.nombre == 'Encargado de Carrera':
                    context['lista_carreras'] = Carrera.objects.filter(encargado=perfil)
                else:
                    context['lista_carreras'] = Carrera.objects.all()
            except Usuario.DoesNotExist:
                context['lista_carreras'] = Carrera.objects.none()
        
        # Eliminamos lista_estados y creamos una lista estática para la IA
        context['niveles_riesgo_ia'] = [
            {'id': '3', 'nombre': 'Riesgo Alto'},
            {'id': '2', 'nombre': 'Riesgo Medio'},
            {'id': '1', 'nombre': 'Riesgo Bajo'},
            {'id': '0', 'nombre': 'Sin Riesgo'},
            {'id': '-1', 'nombre': 'Sin Contacto'},
        ]
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
            perfil = Usuario.objects.get(email=django_user.email)
            if perfil.rol.nombre == 'Tutor':
                return Estudiante.objects.filter(tutor_asignado=perfil)
            elif perfil.rol.nombre == 'Encargado de Carrera':
                carreras_ec = Carrera.objects.filter(encargado=perfil)
                return Estudiante.objects.filter(carrera__in=carreras_ec)
            else:
                return Estudiante.objects.all()
        except Usuario.DoesNotExist:
            return Estudiante.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        estudiante_actual = self.object
        context['bitacoras'] = estudiante_actual.bitacora_set.all().order_by('-fecha_registro')
        context['historial_riesgo'] = HistorialRiesgo.objects.filter(
            estudiante=estudiante_actual
        ).order_by('-fecha_cambio')[:10]
        context['ultimo_historial_ml'] = HistorialRiesgo.objects.filter(
            estudiante=estudiante_actual, origen_cambio='ML'
        ).order_by('-fecha_cambio').first()
        try:
            perfil = Usuario.objects.get(email=self.request.user.email)
            context['es_encargado'] = perfil.rol.nombre == 'Encargado de Carrera'
            context['perfil_usuario'] = perfil
        except Usuario.DoesNotExist:
            context['es_encargado'] = self.request.user.is_superuser
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
                elif perfil.rol.nombre == 'Encargado de Carrera': 
                    es_encargado = True
            except Usuario.DoesNotExist:
                pass 
        
        context['es_tutor'] = es_tutor
        context['es_encargado'] = es_encargado

        # 1. Determinar qué estudiantes ver (Lógica de Permisos)
        if django_user.is_superuser:
            mis_estudiantes = Estudiante.objects.all()
        else:
            try:
                perfil_usuario = Usuario.objects.get(email=django_user.email)
                if perfil_usuario.rol.nombre == 'Tutor':
                    mis_estudiantes = Estudiante.objects.filter(tutor_asignado=perfil_usuario)
                elif perfil_usuario.rol.nombre == 'Encargado de Carrera':
                    # EC solo ve estudiantes de sus carreras asignadas
                    carreras_ec = Carrera.objects.filter(encargado=perfil_usuario)
                    mis_estudiantes = Estudiante.objects.filter(carrera__in=carreras_ec)
                else:
                    mis_estudiantes = Estudiante.objects.all()
            except Usuario.DoesNotExist:
                mis_estudiantes = Estudiante.objects.none()

        # 2. Calcular KPIs (Indicadores) BASADOS EN IA
        total_estudiantes = mis_estudiantes.count()
        
        # Mapeo de Niveles IA
        riesgo_alto = mis_estudiantes.filter(nivel_riesgo_ia__in=[3, 4]).count()
        riesgo_medio = mis_estudiantes.filter(nivel_riesgo_ia=2).count()
        riesgo_bajo = mis_estudiantes.filter(nivel_riesgo_ia=1).count()
        riesgo_sano = mis_estudiantes.filter(nivel_riesgo_ia=0).count()
        riesgo_ghosting = mis_estudiantes.filter(nivel_riesgo_ia=-1).count()

        # Estudiantes pendientes de validación IA (para el nuevo panel)
        context['pendientes_validacion'] = mis_estudiantes.filter(riesgo_pendiente_validacion=True).order_by('-id_estudiante')

        # 3. Bitácoras recientes (de MIS estudiantes)

        ultimas_bitacoras = Bitacora.objects.filter(estudiante__in=mis_estudiantes)
        
        # Filtros (Carrera, Fechas, Alerta)
        carrera_filter = self.request.GET.get('carrera_dashboard')
        if carrera_filter:
            ultimas_bitacoras = ultimas_bitacoras.filter(estudiante__carrera__id_carrera=carrera_filter)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_desde:
            ultimas_bitacoras = ultimas_bitacoras.filter(fecha_registro__date__gte=fecha_desde)
        if fecha_hasta:
            ultimas_bitacoras = ultimas_bitacoras.filter(fecha_registro__date__lte=fecha_hasta)
        
        alerta_filter = self.request.GET.get('tipo_alerta')
        if alerta_filter:
            ultimas_bitacoras = ultimas_bitacoras.filter(alarma__tipo_alarma__id_tipo=alerta_filter)
        
        if not any([carrera_filter, fecha_desde, fecha_hasta, alerta_filter]):
            ultimas_bitacoras = ultimas_bitacoras.order_by('-fecha_registro')[:5]
        else:
            ultimas_bitacoras = ultimas_bitacoras.order_by('-fecha_registro')

        # 4. Inyectar datos al HTML
        context['kpi_total'] = total_estudiantes
        context['kpi_alto'] = riesgo_alto
        context['kpi_medio'] = riesgo_medio
        context['kpi_bajo'] = riesgo_bajo
        context['kpi_sano'] = riesgo_sano
        context['kpi_ghosting'] = riesgo_ghosting
        
        context['ultimas_bitacoras'] = ultimas_bitacoras
        # Filtrar lista de carreras del dashboard según rol
        if django_user.is_superuser:
            context['lista_carreras_dashboard'] = Carrera.objects.all()
        else:
            try:
                perfil_dash = Usuario.objects.get(email=django_user.email)
                if perfil_dash.rol.nombre == 'Encargado de Carrera':
                    context['lista_carreras_dashboard'] = Carrera.objects.filter(encargado=perfil_dash)
                elif perfil_dash.rol.nombre == 'Tutor':
                    ids_c = mis_estudiantes.values_list('carrera', flat=True).distinct()
                    context['lista_carreras_dashboard'] = Carrera.objects.filter(id_carrera__in=ids_c)
                else:
                    context['lista_carreras_dashboard'] = Carrera.objects.all()
            except Usuario.DoesNotExist:
                context['lista_carreras_dashboard'] = Carrera.objects.none()
        context['lista_alertas'] = TipoAlarma.objects.all()

        # Datos para el gráfico [Alto, Medio, Bajo, Sano, Ghosting]
        data_grafico = [riesgo_alto, riesgo_medio, riesgo_bajo, riesgo_sano, riesgo_ghosting] 
        context['data_grafico'] = data_grafico

        # Calcular estudiantes por año de ingreso
        datos_ingreso = mis_estudiantes.values('anio_ingreso').annotate(total=Count('id_estudiante')).order_by('anio_ingreso')
        context['labels_ingreso'] = [str(d['anio_ingreso']) for d in datos_ingreso]
        context['data_ingreso'] = [d['total'] for d in datos_ingreso]
        
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
                
            except ImportError as import_error:
                # Log detallado del error para debugging
                import traceback
                error_detail = traceback.format_exc()
                return HttpResponse(
                    f"Error: No se pudo importar la librería PDF.<br><br>"
                    f"<strong>Detalle del error:</strong><br>"
                    f"<pre>{error_detail}</pre><br>"
                    f"Instala 'xhtml2pdf' (pip install xhtml2pdf==0.2.5)",
                    status=500
                )
            except Exception as general_error:
                # Capturar cualquier otro error durante la generación del PDF
                import traceback
                error_detail = traceback.format_exc()
                return HttpResponse(
                    f"Error al generar PDF:<br><br>"
                    f"<strong>Detalle:</strong><br>"
                    f"<pre>{error_detail}</pre>",
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


class ReporteAsistenciaView(LoginRequiredMixin, ListView):
    model = Estudiante
    template_name = 'sat/asistencia_reporte.html'
    context_object_name = 'estudiantes_data'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        queryset = Estudiante.objects.all()

        # 1. SEGURIDAD: Filtramos según el rol
        if not user.is_superuser:
            try:
                perfil = Usuario.objects.get(email=user.email)
                if perfil.rol.nombre == 'Tutor':
                    queryset = queryset.filter(tutor_asignado=perfil)
                elif perfil.rol.nombre == 'Encargado de Carrera':
                    carreras_ec = Carrera.objects.filter(encargado=perfil)
                    queryset = queryset.filter(carrera__in=carreras_ec)
            except Usuario.DoesNotExist:
                return Estudiante.objects.none()

        # 2. FILTROS DEL USUARIO (Barra de búsqueda)
        q = self.request.GET.get('q')
        carrera = self.request.GET.get('carrera')
        tutor = self.request.GET.get('tutor')

        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(rut__icontains=q))
        if carrera:
            queryset = queryset.filter(carrera__id_carrera=carrera)
        if tutor:
            queryset = queryset.filter(tutor_asignado__id_usuario=tutor)

        # 3. CÁLCULO DE PORCENTAJES (Annotate mágico de Django)
        # Esto cuenta cuántas asistencias totales tiene y cuántas son "Presente"
        queryset = queryset.annotate(
            total_clases=Count('asistencia'),
            clases_presente=Count(Case(
                When(asistencia__estado_asistencia='Presente', then=1),
                output_field=IntegerField()
            ))
        ).order_by('apellido')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filtrar carreras y tutores según el rol
        if user.is_superuser:
            context['carreras'] = Carrera.objects.all()
            context['tutores'] = Usuario.objects.filter(rol__nombre='Tutor')
        else:
            try:
                perfil = Usuario.objects.get(email=user.email)
                if perfil.rol.nombre == 'Tutor':
                    # El tutor no necesita dropdown de carreras ni tutores
                    ids_c = Estudiante.objects.filter(tutor_asignado=perfil).values_list('carrera', flat=True).distinct()
                    context['carreras'] = Carrera.objects.filter(id_carrera__in=ids_c)
                elif perfil.rol.nombre == 'Encargado de Carrera':
                    carreras_ec = Carrera.objects.filter(encargado=perfil)
                    context['carreras'] = carreras_ec
                    # Solo tutores de las carreras del EC
                    context['tutores'] = Usuario.objects.filter(
                        rol__nombre='Tutor', carrera__in=carreras_ec
                    )
                else:
                    context['carreras'] = Carrera.objects.all()
                    context['tutores'] = Usuario.objects.filter(rol__nombre='Tutor')
            except Usuario.DoesNotExist:
                context['carreras'] = Carrera.objects.none()

        return context

class DetalleAsistenciaEstudianteView(LoginRequiredMixin, DetailView):
    model = Estudiante
    template_name = 'sat/asistencia_estudiante_detail.html'
    context_object_name = 'estudiante'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtenemos el historial de asistencias de este alumno
        context['historial_asistencia'] = Asistencia.objects.filter(
            estudiante=self.object
        ).select_related('tutoria').order_by('-tutoria__fecha')
        
        # Calculamos stats simples para la cabecera
        total = context['historial_asistencia'].count()
        presentes = context['historial_asistencia'].filter(estado_asistencia='Presente').count()
        context['porcentaje'] = (presentes / total * 100) if total > 0 else 0
        return context


@login_required
def sobrescribir_riesgo(request, pk):
    """
    El EC corrige el riesgo: ACTUALIZA nivel_riesgo_ia directamente (el EC toma el control).
    Guarda nivel_riesgo_manual como etiqueta de reentrenamiento para el modelo.
    Limpia riesgo_pendiente_validacion porque el EC ya actuó.
    """
    from django.utils import timezone

    estudiante = get_object_or_404(Estudiante, pk=pk)

    try:
        perfil = Usuario.objects.get(email=request.user.email)
        if perfil.rol.nombre != 'Encargado de Carrera' and not request.user.is_superuser:
            messages.error(request, '⛔ Solo los Encargados de Carrera pueden corregir el riesgo.')
            return redirect('estudiante-detail', pk=pk)
    except Usuario.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permisos para esta acción.')
            return redirect('estudiante-detail', pk=pk)
        perfil = None

    if request.method == 'POST':
        riesgo_manual_str = request.POST.get('riesgo_manual', '')
        observacion = request.POST.get('observacion_sobrescritura', '').strip()

        if not riesgo_manual_str:
            messages.error(request, '❌ Debes seleccionar un nivel de riesgo.')
            return redirect('estudiante-detail', pk=pk)

        try:
            riesgo_manual = int(riesgo_manual_str)
            if riesgo_manual not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            messages.error(request, '❌ Nivel de riesgo inválido.')
            return redirect('estudiante-detail', pk=pk)

        # El EC toma el control: nivel_riesgo_ia = valor del EC (es el último que actúa)
        # nivel_riesgo_manual queda como etiqueta de reentrenamiento
        estudiante.nivel_riesgo_ia = riesgo_manual          # ← valor que se muestra
        estudiante.nivel_riesgo_manual = riesgo_manual      # ← etiqueta para reentrenamiento
        estudiante.riesgo_sobrescrito = True                # ← indica que el EC fue el último
        estudiante.riesgo_pendiente_validacion = False      # ← el EC ya validó, no hay pendiente
        estudiante.observacion_sobrescritura = observacion or None
        estudiante.riesgo_corregido_por = perfil
        estudiante.riesgo_corregido_fecha = timezone.now()
        estudiante.save(update_fields=[
            'nivel_riesgo_ia', 'nivel_riesgo_manual', 'riesgo_sobrescrito',
            'riesgo_pendiente_validacion', 'observacion_sobrescritura',
            'riesgo_corregido_por', 'riesgo_corregido_fecha'
        ])

        nivel_nombre = {0: 'Sin Riesgo', 1: 'Bajo', 2: 'Medio', 3: 'Alto'}.get(riesgo_manual, '?')
        messages.success(
            request,
            f'✅ Corrección guardada: {estudiante.nombre} {estudiante.apellido} → "{nivel_nombre}". Etiqueta registrada para reentrenamiento.'
        )
        return redirect('estudiante-detail', pk=pk)

    return redirect('estudiante-detail', pk=pk)


@login_required
def eliminar_historial_riesgo(request, pk):
    """
    Permite a Encargados de Carrera eliminar un registro erróneo del historial de riesgo.
    Reutiliza el modal de confirmación existente en el template.
    """
    historial = get_object_or_404(HistorialRiesgo, pk=pk)
    estudiante_pk = historial.estudiante.pk

    try:
        perfil = Usuario.objects.get(email=request.user.email)
        if perfil.rol.nombre != 'Encargado de Carrera' and not request.user.is_superuser:
            messages.error(request, '⛔ Solo los Encargados de Carrera pueden eliminar registros del historial.')
            return redirect('estudiante-detail', pk=estudiante_pk)
    except Usuario.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permisos.')
            return redirect('estudiante-detail', pk=estudiante_pk)

    if request.method == 'POST':
        historial.delete()
        messages.success(request, '✅ Registro de historial eliminado correctamente.')

    return redirect('estudiante-detail', pk=estudiante_pk)


@login_required
def recalcular_riesgo_estudiante(request, pk):
    """
    Recalcula el riesgo IA para UN estudiante específico de forma síncrona.
    Accesible para Tutores y Encargados de Carrera (y superusuarios).
    El resultado aparece inmediatamente en la página del estudiante.
    """
    from .services import PredictorRiesgo

    estudiante = get_object_or_404(Estudiante, pk=pk)

    if request.method == 'POST':
        try:
            predictor = PredictorRiesgo()
            if not predictor.cerebro:
                messages.error(request, '❌ El modelo IA no está disponible. Contacta al administrador.')
                return redirect('estudiante-detail', pk=pk)

            riesgo_anterior = estudiante.nivel_riesgo_ia
            nuevo_riesgo = predictor.predecir_estudiante(estudiante)

            if nuevo_riesgo != riesgo_anterior or estudiante.riesgo_sobrescrito:
                # IA toma el control: actualiza nivel_riesgo_ia y marca como pendiente de validación
                estudiante.nivel_riesgo_ia = nuevo_riesgo
                campos = ['nivel_riesgo_ia', 'riesgo_pendiente_validacion']
                if nuevo_riesgo != riesgo_anterior:
                    estudiante.riesgo_pendiente_validacion = True   # EC debe confirmar este cambio
                if estudiante.riesgo_sobrescrito:
                    estudiante.riesgo_sobrescrito = False  # La etiqueta manual sigue en nivel_riesgo_manual
                    campos.append('riesgo_sobrescrito')
                estudiante.save(update_fields=campos)

                nivel_nombre = {-1: 'Sin Contacto', 0: 'Sin Riesgo', 1: 'Bajo', 2: 'Medio', 3: 'Alto'}.get(nuevo_riesgo, '?')
                messages.success(
                    request,
                    f'🤖 Riesgo actualizado: {riesgo_anterior} → {nuevo_riesgo} ({nivel_nombre}). '
                    f'⏳ Pendiente de confirmación por el Encargado de Carrera.'
                )
            else:
                messages.info(request, f'ℹ️ El riesgo no cambió (sigue en nivel {riesgo_anterior}).')

        except Exception as e:
            messages.error(request, f'❌ Error al recalcular: {e}')

    return redirect('estudiante-detail', pk=pk)


@login_required
def recalcular_riesgo_masivo(request):
    """
    Recalcula el riesgo IA para TODOS los estudiantes o para una CARRERA específica.
    Solo accesible para Encargados de Carrera y superusuarios.
    Muestra un resumen al terminar.
    """
    from .services import PredictorRiesgo

    # Seguridad: solo Encargados o superusuarios
    try:
        perfil = Usuario.objects.get(email=request.user.email)
        if perfil.rol.nombre != 'Encargado de Carrera' and not request.user.is_superuser:
            messages.error(request, '⛔ Solo los Encargados de Carrera pueden ejecutar el recálculo masivo.')
            return redirect('home')
    except Usuario.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permisos.')
            return redirect('home')

    if request.method == 'POST':
        carrera_id = request.POST.get('carrera_id', '').strip()

        # Filtrar por carrera o tomar todos
        qs = Estudiante.objects.all()
        if carrera_id:
            qs = qs.filter(carrera__id_carrera=carrera_id)
            scope_label = Carrera.objects.filter(id_carrera=carrera_id).values_list('nombre', flat=True).first() or 'Carrera desconocida'
        else:
            scope_label = 'todos los estudiantes'

        total = qs.count()
        if total == 0:
            messages.warning(request, '⚠️ No se encontraron estudiantes con ese filtro.')
            return redirect('home')

        # Cargar modelo UNA vez
        try:
            predictor = PredictorRiesgo()
            if not predictor.cerebro:
                messages.error(request, '❌ El modelo IA no está disponible.')
                return redirect('home')
        except Exception as e:
            messages.error(request, f'❌ Error al cargar el modelo: {e}')
            return redirect('home')

        actualizados = 0
        sin_cambio = 0
        errores = 0

        for estudiante in qs.iterator():
            try:
                nuevo_riesgo = predictor.predecir_estudiante(estudiante)
                hubo_cambio_riesgo = nuevo_riesgo != estudiante.nivel_riesgo_ia
                tiene_override = estudiante.riesgo_sobrescrito

                if hubo_cambio_riesgo or tiene_override:
                    estudiante.nivel_riesgo_ia = nuevo_riesgo
                    campos = ['nivel_riesgo_ia']
                    if tiene_override:
                        # La IA toma el control; la etiqueta manual queda preservada en nivel_riesgo_manual
                        estudiante.riesgo_sobrescrito = False
                        campos.append('riesgo_sobrescrito')
                    estudiante.save(update_fields=campos)
                    actualizados += 1
                else:
                    sin_cambio += 1
            except Exception:
                errores += 1

        msg = (
            f'🤖 Recálculo completado para {scope_label}: '
            f'{total} estudiantes procesados — '
            f'{actualizados} actualizados, {sin_cambio} sin cambio'
        )
        if errores:
            msg += f', {errores} con error'
        if actualizados > 0:
            msg += f'. ⏳ {actualizados} estudiante(s) pendiente(s) de confirmación.'
        messages.success(request, msg)

    return redirect('home')


@login_required
def confirmar_prediccion_ia(request, pk):
    """
    El EC confirma la predicción IA sin cambiarla.
    Simplemente limpia riesgo_pendiente_validacion = False.
    Solo Encargados de Carrera y superusuarios pueden confirmar.
    """
    estudiante = get_object_or_404(Estudiante, pk=pk)

    try:
        perfil = Usuario.objects.get(email=request.user.email)
        if perfil.rol.nombre != 'Encargado de Carrera' and not request.user.is_superuser:
            messages.error(request, '⛔ Solo los Encargados de Carrera pueden confirmar predicciones.')
            return redirect('estudiante-detail', pk=pk)
    except Usuario.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permisos.')
            return redirect('estudiante-detail', pk=pk)

    if request.method == 'POST':
        nivel_nombre = {-1: 'Sin Contacto', 0: 'Sin Riesgo', 1: 'Bajo', 2: 'Medio', 3: 'Alto'}.get(estudiante.nivel_riesgo_ia, '?')
        estudiante.riesgo_pendiente_validacion = False
        estudiante.save(update_fields=['riesgo_pendiente_validacion'])
        messages.success(
            request,
            f'✅ Predicción confirmada: {estudiante.nombre} {estudiante.apellido} → Nivel {nivel_nombre}.'
        )

    return redirect('estudiante-detail', pk=pk)


@login_required
def rechazar_prediccion_ia(request, pk):
    """
    El EC rechaza la nueva predicción de la IA.
    Se busca el último historial de riesgo para restaurar el valor anterior,
    y se guarda como una corrección manual.
    """
    from django.utils import timezone
    estudiante = get_object_or_404(Estudiante, pk=pk)

    try:
        perfil = Usuario.objects.get(email=request.user.email)
        if perfil.rol.nombre != 'Encargado de Carrera' and not request.user.is_superuser:
            messages.error(request, '⛔ Solo los Encargados de Carrera pueden rechazar predicciones.')
            return redirect('estudiante-detail', pk=pk)
    except Usuario.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permisos.')
            return redirect('estudiante-detail', pk=pk)

    if request.method == 'POST':
        if not estudiante.riesgo_pendiente_validacion:
            messages.warning(request, '⚠️ No hay predicción pendiente que rechazar.')
            return redirect('estudiante-detail', pk=pk)

        # Buscar el último cambio hecho por la IA (el que estamos rechazando)
        ultimo_historial = HistorialRiesgo.objects.filter(
            estudiante=estudiante, origen_cambio='ML'
        ).order_by('-fecha_cambio').first()

        riesgo_anterior = ultimo_historial.riesgo_anterior if ultimo_historial else 0

        # Rechazar implica que el EC toma el control restaurando el riesgo anterior
        estudiante.nivel_riesgo_ia = riesgo_anterior
        estudiante.nivel_riesgo_manual = riesgo_anterior
        estudiante.riesgo_sobrescrito = True
        estudiante.riesgo_pendiente_validacion = False
        estudiante.observacion_sobrescritura = "Predicción IA rechazada por EC. Se restauró el nivel previo."
        estudiante.riesgo_corregido_por = perfil if perfil else None
        estudiante.riesgo_corregido_fecha = timezone.now()
        
        # Guardar todo. El signal pre_save generará el nuevo Historial originado por 'HU'
        estudiante.save(update_fields=[
            'nivel_riesgo_ia', 'nivel_riesgo_manual', 'riesgo_sobrescrito',
            'riesgo_pendiente_validacion', 'observacion_sobrescritura',
            'riesgo_corregido_por', 'riesgo_corregido_fecha'
        ])

        nivel_estaba = {-1: 'Sin Contacto', 0: 'Sin Riesgo', 1: 'Bajo', 2: 'Medio', 3: 'Alto'}.get(riesgo_anterior, '?')
        messages.success(
            request,
            f'🙅 Predicción rechazada para {estudiante.nombre}. Riesgo restaurado a: Nivel {nivel_estaba}.'
        )

    return redirect('estudiante-detail', pk=pk)


# ═══════════════════════════════════════════════════════════════════
# BLOQUE 2: CRUD ADMINISTRATIVO (solo superuser)
# ═══════════════════════════════════════════════════════════════════

class SuperuserRequiredMixin:
    """Mixin que restringe el acceso solo a superusers."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permiso para acceder a esa sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


def superuser_required(view_func):
    """Decorador equivalente para vistas de función."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, '⛔ No tienes permiso para acceder a esa sección.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Panel principal de administración ─────────────────────────────
class AdminPanelView(SuperuserRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'sat/admin/admin_panel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_usuarios'] = Usuario.objects.count()
        context['total_carreras'] = Carrera.objects.count()
        context['total_ec'] = Usuario.objects.filter(rol__nombre='Encargado de Carrera').count()
        context['total_tutores'] = Usuario.objects.filter(rol__nombre='Tutor').count()
        context['total_tipo_alarma'] = TipoAlarma.objects.count()
        context['total_tipo_tutoria'] = TipoTutoria.objects.count()
        context['total_clasificacion'] = ClasificacionTutoria.objects.count()
        return context


# ── CRUD Usuarios ──────────────────────────────────────────────────
class AdminUsuarioListView(SuperuserRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'sat/admin/admin_usuario_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Usuario.objects.select_related('rol', 'carrera').order_by('rol__nombre', 'apellido')

        rol_filter = self.request.GET.get('rol')
        carrera_filter = self.request.GET.get('carrera')
        q = self.request.GET.get('q')

        if rol_filter:
            qs = qs.filter(rol__id_rol=rol_filter)
        if carrera_filter:
            qs = qs.filter(carrera__id_carrera=carrera_filter)
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(email__icontains=q))

        # Anotar si el auth.User está activo
        usuarios_data = []
        for u in qs:
            auth_user = User.objects.filter(email=u.email).first()
            usuarios_data.append({
                'perfil': u,
                'activo': auth_user.is_active if auth_user else None,
                'username': auth_user.username if auth_user else '—',
                'is_superuser': auth_user.is_superuser if auth_user else False,
            })

        # Paginación
        paginator = Paginator(usuarios_data, 20)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['is_paginated'] = paginator.num_pages > 1
        context['roles'] = Rol.objects.all()
        context['carreras'] = Carrera.objects.all()
        return context


@superuser_required
@login_required
def admin_usuario_create(request):
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            pw = cd['password'].strip()
            if not pw:
                messages.error(request, 'Debes ingresar una contraseña para un usuario nuevo.')
                return render(request, 'sat/admin/admin_usuario_form.html', {'form': form, 'accion': 'Crear'})
            try:
                with transaction.atomic():
                    auth_user = User.objects.create_user(
                        username=cd['username'],
                        email=cd['email'],
                        password=pw,
                        first_name=cd['nombre'],
                        last_name=cd['apellido'],
                    )
                    Usuario.objects.create(
                        rut=cd['rut'],
                        nombre=cd['nombre'],
                        apellido=cd['apellido'],
                        email=cd['email'],
                        password='managed-by-django-auth',
                        rol=cd['rol'],
                        carrera=cd.get('carrera'),
                    )
                messages.success(request, f'✅ Usuario {cd["username"]} creado correctamente.')
                return redirect('admin-usuario-list')
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {e}')
    else:
        form = UsuarioAdminForm()
    return render(request, 'sat/admin/admin_usuario_form.html', {'form': form, 'accion': 'Crear'})


@superuser_required
@login_required
def admin_usuario_edit(request, pk):
    perfil = get_object_or_404(Usuario, pk=pk)
    auth_user = User.objects.filter(email=perfil.email).first()

    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # Actualizar sat.Usuario
                    perfil.nombre   = cd['nombre']
                    perfil.apellido = cd['apellido']
                    perfil.rut      = cd['rut']
                    perfil.email    = cd['email']
                    perfil.rol      = cd['rol']
                    perfil.carrera  = cd.get('carrera')
                    perfil.save()
                    # Actualizar auth.User
                    if auth_user:
                        auth_user.first_name = cd['nombre']
                        auth_user.last_name  = cd['apellido']
                        auth_user.email      = cd['email']
                        auth_user.username   = cd['username']
                        if cd['password']:
                            auth_user.set_password(cd['password'])
                        auth_user.save()
                messages.success(request, f'✅ Usuario {perfil.get_full_name()} actualizado.')
                return redirect('admin-usuario-list')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {e}')
    else:
        form = UsuarioAdminForm(initial={
            'nombre':   perfil.nombre,
            'apellido': perfil.apellido,
            'rut':      perfil.rut,
            'email':    perfil.email,
            'username': auth_user.username if auth_user else '',
            'rol':      perfil.rol,
            'carrera':  perfil.carrera,
        })
    return render(request, 'sat/admin/admin_usuario_form.html', {
        'form': form, 'accion': 'Editar', 'perfil': perfil
    })


@superuser_required
@login_required
def admin_usuario_toggle(request, pk):
    """Activa / Desactiva el login de un usuario (no lo borra)."""
    perfil = get_object_or_404(Usuario, pk=pk)
    auth_user = User.objects.filter(email=perfil.email).first()
    if auth_user:
        if auth_user.is_superuser:
            messages.error(request, '⛔ No puedes desactivar al superuser.')
        else:
            auth_user.is_active = not auth_user.is_active
            auth_user.save()
            estado = 'activado' if auth_user.is_active else 'desactivado'
            messages.success(request, f'Usuario {perfil.get_full_name()} {estado}.')
    return redirect('admin-usuario-list')


@superuser_required
@login_required
def admin_generar_password(request):
    """Genera una contraseña segura aleatoria y la devuelve como JSON."""
    from django.http import JsonResponse
    alphabet = string.ascii_letters + string.digits + '!@#$%&'
    pw = ''.join(secrets.choice(alphabet) for _ in range(12))
    return JsonResponse({'password': pw})


# ── CRUD Carreras ──────────────────────────────────────────────────
class AdminCarreraListView(SuperuserRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'sat/admin/admin_carrera_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carreras = Carrera.objects.select_related('encargado').order_by('nombre')
        carrera_data = []
        for c in carreras:
            total_alumnos = Estudiante.objects.filter(carrera=c).count()
            total_tutores = Usuario.objects.filter(rol__nombre='Tutor', carrera=c).count()
            carrera_data.append({
                'carrera': c,
                'total_alumnos': total_alumnos,
                'total_tutores': total_tutores,
                'puede_eliminar': total_alumnos == 0,
            })

        # Paginación
        paginator = Paginator(carrera_data, 15)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['is_paginated'] = paginator.num_pages > 1
        return context


@superuser_required
@login_required
def admin_carrera_create(request):
    if request.method == 'POST':
        form = CarreraAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Carrera "{form.cleaned_data["nombre"]}" creada.')
            return redirect('admin-carrera-list')
    else:
        form = CarreraAdminForm()
    return render(request, 'sat/admin/admin_carrera_form.html', {'form': form, 'accion': 'Crear'})


@superuser_required
@login_required
def admin_carrera_edit(request, pk):
    carrera = get_object_or_404(Carrera, pk=pk)
    if request.method == 'POST':
        form = CarreraAdminForm(request.POST, instance=carrera)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Carrera "{carrera.nombre}" actualizada.')
            return redirect('admin-carrera-list')
    else:
        form = CarreraAdminForm(instance=carrera)
    return render(request, 'sat/admin/admin_carrera_form.html', {
        'form': form, 'accion': 'Editar', 'carrera': carrera
    })


@superuser_required
@login_required
def admin_carrera_delete(request, pk):
    carrera = get_object_or_404(Carrera, pk=pk)
    if Estudiante.objects.filter(carrera=carrera).exists():
        messages.error(request, f'⛔ No se puede eliminar "{carrera.nombre}" porque tiene estudiantes asociados.')
        return redirect('admin-carrera-list')
    if request.method == 'POST':
        nombre = carrera.nombre
        carrera.delete()
        messages.success(request, f'🗑️ Carrera "{nombre}" eliminada.')
        return redirect('admin-carrera-list')
    return render(request, 'sat/admin/admin_carrera_confirm_delete.html', {'carrera': carrera})


# ── Tablas Maestras (panel unificado) ──────────────────────────────
@superuser_required
@login_required
def admin_maestras(request):
    context = {
        'tipos_alarma': TipoAlarma.objects.all().order_by('nombre'),
        'tipos_tutoria': TipoTutoria.objects.all().order_by('nombre'),
        'clasificaciones': ClasificacionTutoria.objects.all().order_by('nombre'),
        'tipos_desercion': TipoDesercion.objects.all().order_by('causa'),
        'estados': Estado.objects.all().order_by('nombre'),
        'forma_alarma': TipoAlarmaForm(),
        'forma_tutoria': TipoTutoriaForm(),
        'forma_clasificacion': ClasificacionTutoriaForm(),
        'forma_desercion': TipoDesercionForm(),
        'forma_estado': EstadoForm(),
    }
    return render(request, 'sat/admin/admin_maestras.html', context)


@superuser_required
@login_required
def admin_maestra_accion(request, modelo, pk=None):
    """
    Vista unificada para crear/editar/eliminar cualquier tabla maestra.
    modelo: 'tipo-alarma' | 'tipo-tutoria' | 'clasificacion' | 'tipo-desercion' | 'estado'
    """
    MODEL_MAP = {
        'tipo-alarma':    (TipoAlarma,          TipoAlarmaForm,          'id_tipo',          'nombre'),
        'tipo-tutoria':   (TipoTutoria,         TipoTutoriaForm,         'id_tipo',          'nombre'),
        'clasificacion':  (ClasificacionTutoria, ClasificacionTutoriaForm,'id_clasificacion', 'nombre'),
        'tipo-desercion': (TipoDesercion,        TipoDesercionForm,       'id_tipo_desercion','causa'),
        'estado':         (Estado,               EstadoForm,              'id_estado',        'nombre'),
    }
    if modelo not in MODEL_MAP:
        messages.error(request, 'Modelo no reconocido.')
        return redirect('admin-maestras')

    ModelClass, FormClass, pk_field, label_field = MODEL_MAP[modelo]
    accion = request.POST.get('accion') or request.GET.get('accion', 'crear')

    if accion == 'eliminar' and pk:
        obj = get_object_or_404(ModelClass, **{pk_field: pk})
        try:
            nombre_obj = getattr(obj, label_field)
            obj.delete()
            messages.success(request, f'🗑️ Eliminado: "{nombre_obj}".')
        except Exception as e:
            messages.error(request, f'No se puede eliminar: {e}')
        return redirect('admin-maestras')

    if pk:
        obj = get_object_or_404(ModelClass, **{pk_field: pk})
        form = FormClass(request.POST or None, instance=obj)
    else:
        form = FormClass(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '✅ Guardado correctamente.')
        return redirect('admin-maestras')

    messages.error(request, 'Formulario con errores. Verifica los campos.')
    return redirect('admin-maestras')
