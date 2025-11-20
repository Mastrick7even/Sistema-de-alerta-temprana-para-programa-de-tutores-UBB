from django.urls import path
from .views import EstudianteListView

urlpatterns = [
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante-list'),
]