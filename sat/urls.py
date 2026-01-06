from django.urls import path
from .views import EstudianteListView, EstudianteDetailView, BitacoraCreateView, BitacoraUpdateView, BitacoraDeleteView, DashboardView, ReporteEstudiantePDF, MisTutoriasView, tomar_asistencia, TutoriaCreateView, TutoriaUpdateView, TutoriaDeleteView, leer_notificacion, todas_notificaciones, marcar_notificaciones_leidas, eliminar_notificaciones

urlpatterns = [
    path('', DashboardView.as_view(), name='home'), 
    path('dashboard/', DashboardView.as_view(), name='dashboard'), # Alias opcional
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiantes/<int:pk>/', EstudianteDetailView.as_view(), name='estudiante-detail'),
    path('estudiantes/<int:pk>/bitacora/nueva/', BitacoraCreateView.as_view(), name='bitacora-create'),
    # Editar: /bitacora/123/editar/
    path('bitacora/<int:pk>/editar/', BitacoraUpdateView.as_view(), name='bitacora-update'),
    # Borrar: /bitacora/123/borrar/
    path('bitacora/<int:pk>/borrar/', BitacoraDeleteView.as_view(), name='bitacora-delete'),
    # PDF: /estudiante/123/pdf/
    path('estudiante/<int:pk>/pdf/', ReporteEstudiantePDF.as_view(), name='estudiante-pdf'),
    path('tutorias/', MisTutoriasView.as_view(), name='mis-tutorias'),
    path('tutorias/nueva/', TutoriaCreateView.as_view(), name='crear-tutoria'),
    path('tutorias/<int:pk>/editar/', TutoriaUpdateView.as_view(), name='tutoria-update'),
    path('tutorias/<int:pk>/borrar/', TutoriaDeleteView.as_view(), name='tutoria-delete'),
    path('tutorias/<int:pk>/asistencia/', tomar_asistencia, name='tomar-asistencia'),
    path('notificacion/<int:pk>/leer/', leer_notificacion, name='leer-notificacion'),
    path('notificaciones/', todas_notificaciones, name='todas-notificaciones'),
    path('notificaciones/marcar-leidas/', marcar_notificaciones_leidas, name='marcar-notificaciones-leidas'),
    path('notificaciones/eliminar/', eliminar_notificaciones, name='eliminar-notificaciones'),
]
