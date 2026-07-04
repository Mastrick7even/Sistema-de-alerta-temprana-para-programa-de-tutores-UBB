from django.urls import path
from .views import (
    EstudianteListView, EstudianteDetailView, BitacoraCreateView, BitacoraUpdateView, BitacoraDeleteView, agregar_comentario_bitacora,
    editar_comentario_bitacora, eliminar_comentario_bitacora,
    DashboardView, ReporteEstudiantePDF, MisTutoriasView, tomar_asistencia, TutoriaCreateView, TutoriaUpdateView, TutoriaDeleteView,
    leer_notificacion, todas_notificaciones, marcar_notificaciones_leidas, eliminar_notificaciones, ReporteAsistenciaView,
    DetalleAsistenciaEstudianteView, sobrescribir_riesgo, eliminar_historial_riesgo,
    recalcular_riesgo_estudiante, recalcular_riesgo_masivo, confirmar_prediccion_ia, rechazar_prediccion_ia,
    # Bloque 2: Admin CRUD
    AdminPanelView, AdminUsuarioListView, admin_usuario_create, admin_usuario_edit, admin_usuario_toggle,
    AdminCarreraListView, admin_carrera_create, admin_carrera_edit, admin_carrera_delete,
    admin_maestras, admin_maestra_accion, admin_generar_password,
    # Bloque 3: Gestión Tutores EC
    EcTutoresView, EcTutorDetalleView, ec_reasignar_estudiante, ec_reasignar_todo, ec_asignar_alumnos, ec_acciones_masivas_tutorados,
    # Bloque 4: Carga Masiva
    CargaMasivaView, descargar_errores_carga_masiva, descargar_plantilla_carga_masiva
)

urlpatterns = [
    path('', DashboardView.as_view(), name='home'), 
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiantes/<int:pk>/', EstudianteDetailView.as_view(), name='estudiante-detail'),
    path('estudiantes/<int:pk>/bitacora/nueva/', BitacoraCreateView.as_view(), name='bitacora-create'),
    path('bitacora/<int:pk>/editar/', BitacoraUpdateView.as_view(), name='bitacora-update'),
    path('bitacora/<int:pk>/borrar/', BitacoraDeleteView.as_view(), name='bitacora-delete'),
    path('bitacora/<int:pk>/comentario/nuevo/', agregar_comentario_bitacora, name='agregar-comentario-bitacora'),
    path('comentario/<int:pk>/editar/', editar_comentario_bitacora, name='editar-comentario-bitacora'),
    path('comentario/<int:pk>/eliminar/', eliminar_comentario_bitacora, name='eliminar-comentario-bitacora'),
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

    # ── Bloque 2: CRUD Administrativo (solo superuser) ────────────────
    path('admin-sat/', AdminPanelView.as_view(), name='admin-panel'),
    path('admin-sat/usuarios/', AdminUsuarioListView.as_view(), name='admin-usuario-list'),
    path('admin-sat/usuarios/nuevo/', admin_usuario_create, name='admin-usuario-create'),
    path('admin-sat/usuarios/<int:pk>/editar/', admin_usuario_edit, name='admin-usuario-edit'),
    path('admin-sat/usuarios/<int:pk>/toggle/', admin_usuario_toggle, name='admin-usuario-toggle'),
    path('admin-sat/usuarios/generar-password/', admin_generar_password, name='admin-generar-password'),
    path('admin-sat/carreras/', AdminCarreraListView.as_view(), name='admin-carrera-list'),
    path('admin-sat/carreras/nueva/', admin_carrera_create, name='admin-carrera-create'),
    path('admin-sat/carreras/<int:pk>/editar/', admin_carrera_edit, name='admin-carrera-edit'),
    path('admin-sat/carreras/<int:pk>/eliminar/', admin_carrera_delete, name='admin-carrera-delete'),
    path('admin-sat/maestras/', admin_maestras, name='admin-maestras'),
    path('admin-sat/maestras/<str:modelo>/', admin_maestra_accion, name='admin-maestra-crear'),
    path('admin-sat/maestras/<str:modelo>/<int:pk>/', admin_maestra_accion, name='admin-maestra-editar'),
    path('admin-sat/carga-masiva/', CargaMasivaView.as_view(), name='admin-carga-masiva'),
    path('admin-sat/carga-masiva/descargar-plantilla/', descargar_plantilla_carga_masiva, name='admin-descargar-plantilla'),
    path('admin-sat/carga-masiva/descargar-errores/', descargar_errores_carga_masiva, name='admin-descargar-errores'),

    # ── Bloque 3: Gestión Tutores para EC ──────────────────────────
    path('ec/tutores/', EcTutoresView.as_view(), name='ec-tutores'),
    path('ec/tutores/<int:pk>/', EcTutorDetalleView.as_view(), name='ec-tutor-detalle'),
    path('ec/tutores/<int:pk>/reasignar-todo/', ec_reasignar_todo, name='ec-reasignar-todo'),
    path('ec/estudiantes/<int:pk>/reasignar/', ec_reasignar_estudiante, name='ec-reasignar-estudiante'),
    path('ec/tutores/<int:pk>/asignar/', ec_asignar_alumnos, name='ec-asignar-alumnos'),
    path('ec/tutores/<int:pk>/acciones-masivas/', ec_acciones_masivas_tutorados, name='ec-acciones-masivas-tutorados'),
]
