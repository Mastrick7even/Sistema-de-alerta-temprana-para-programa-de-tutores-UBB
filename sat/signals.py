from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bitacora, Notificacion, Usuario, Rol

# IMPORTANTE: Este signal está temporalmente desactivado porque el modelo Bitacora
# no tiene el campo 'autor'. Ver recomendaciones al final del archivo.

@receiver(post_save, sender=Bitacora)
def notificar_observacion(sender, instance, created, **kwargs):
    if created:
        # instance es la Bitácora recién creada
        autor = instance.autor
        estudiante = instance.estudiante
        
        # Lógica: Si el autor es Tutor, notificar a los Encargados
        if autor and autor.rol.nombre == 'Tutor':
            # Buscamos a todos los usuarios con rol 'Encargado'
            # (O podrías filtrar por el Encargado de LA carrera del estudiante si tienes esa relación)
            encargados = Usuario.objects.filter(rol__nombre='Encargado de Carrera')
            
            # Crear mensaje con la observación
            observacion_texto = instance.observacion if instance.observacion else "Sin detalle"
            mensaje = f"📝 {observacion_texto}"
            
            for encargado in encargados:
                Notificacion.objects.create(
                    destinatario=encargado,
                    actor=autor,
                    mensaje=mensaje,
                    estudiante_relacionado=estudiante
                )

