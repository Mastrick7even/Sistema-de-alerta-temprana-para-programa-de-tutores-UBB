from django.urls import path
from .views import EstudianteListView, EstudianteDetailView, BitacoraCreateView

urlpatterns = [
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiantes/<int:pk>/', EstudianteDetailView.as_view(), name='estudiante-detail'),
    path('estudiantes/<int:pk>/bitacora/nueva/', BitacoraCreateView.as_view(), name='bitacora-create'),
]