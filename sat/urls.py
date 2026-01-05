from django.urls import path
from .views import EstudianteListView, EstudianteDetailView, BitacoraCreateView, BitacoraUpdateView, BitacoraDeleteView, DashboardView

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
]
