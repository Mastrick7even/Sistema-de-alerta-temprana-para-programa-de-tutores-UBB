from django.contrib import admin

# Register your models here.

from .models import (
    Usuario, Rol, Carrera, Estudiante, 
    Estado, TipoDesercion, HistorialEstado,
    Tutoria, TipoTutoria, ClasificacionTutoria, Asistencia,
    Bitacora, Alarma, TipoAlarma
)

# Registro básico de modelos
# Esto hace que aparezcan en el panel tal cual
admin.site.register(Rol)
admin.site.register(Carrera)
admin.site.register(Estado)
admin.site.register(TipoDesercion)
admin.site.register(TipoTutoria)
admin.site.register(ClasificacionTutoria)
admin.site.register(TipoAlarma)

# Para modelos más complejos, podemos personalizar cómo se ven (opcional por ahora)
admin.site.register(Usuario)
admin.site.register(Estudiante)
admin.site.register(HistorialEstado)
admin.site.register(Tutoria)
admin.site.register(Asistencia)
admin.site.register(Bitacora)
admin.site.register(Alarma)