from django.urls import path
from .views import (
    EstudianteListView, EstudianteDetailView, BitacoraCreateView, BitacoraUpdateView, BitacoraDeleteView, 
    DashboardView, ReporteEstudiantePDF, MisTutoriasView, tomar_asistencia, TutoriaCreateView, TutoriaUpdateView, TutoriaDeleteView, 
    leer_notificacion, todas_notificaciones, marcar_notificaciones_leidas, eliminar_notificaciones, ReporteAsistenciaView,
    DetalleAsistenciaEstudianteView, sobrescribir_riesgo, eliminar_historial_riesgo,
    recalcular_riesgo_estudiante, recalcular_riesgo_masivo, confirmar_prediccion_ia, rechazar_prediccion_ia
)

urlpatterns = [
    path('', DashboardView.as_view(), name='home'), 
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiantes/<int:pk>/', EstudianteDetailView.as_view(), name='estudiante-detail'),
    path('estudiantes/<int:pk>/bitacora/nueva/', BitacoraCreateView.as_view(), name='bitacora-create'),
    path('bitacora/<int:pk>/editar/', BitacoraUpdateView.as_view(), name='bitacora-update'),
    path('bitacora/<int:pk>/borrar/', BitacoraDeleteView.as_view(), name='bitacora-delete'),
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
    path('asistencia/reporte/', ReporteAsistenciaView.as_view(), name='asistencia-reporte'),
    path('asistencia/estudiante/<int:pk>/', DetalleAsistenciaEstudianteView.as_view(), name='asistencia-detalle'),
    path('estudiantes/<int:pk>/sobrescribir-riesgo/', sobrescribir_riesgo, name='sobrescribir-riesgo'),
    path('historial-riesgo/<int:pk>/eliminar/', eliminar_historial_riesgo, name='eliminar-historial-riesgo'),
    path('estudiantes/<int:pk>/recalcular-riesgo/', recalcular_riesgo_estudiante, name='recalcular-riesgo-estudiante'),
    path('recalcular-riesgo-masivo/', recalcular_riesgo_masivo, name='recalcular-riesgo-masivo'),
    path('estudiantes/<int:pk>/confirmar-prediccion/', confirmar_prediccion_ia, name='confirmar-prediccion-ia'),
    path('estudiantes/<int:pk>/rechazar-prediccion/', rechazar_prediccion_ia, name='rechazar-prediccion-ia'),
]
