from django.urls import path
from .views import EstudianteListView, EstudianteDetailView

urlpatterns = [
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiantes/<int:pk>/', EstudianteDetailView.as_view(), name='estudiante-detail'),
]