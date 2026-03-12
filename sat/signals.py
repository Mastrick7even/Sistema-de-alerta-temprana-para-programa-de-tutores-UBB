from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Bitacora, Notificacion, Usuario, Rol
from .services import PredictorRiesgo


@receiver(post_save, sender=Bitacora)
def notificar_observacion(sender, instance, created, **kwargs):
    if created:
        # instance es la Bitácora recién creada
        autor = instance.autor
        estudiante = instance.estudiante

        # Solo notificar si el estudiante tiene riesgo Medio (2) o Alto (3/4)
        nivel_riesgo = estudiante.get_nivel_riesgo_efectivo()
        if nivel_riesgo < 1:
            return

        # Lógica: Si el autor es Tutor, notificar a los Encargados
        if autor and autor.rol.nombre == 'Tutor':
            # Buscamos a todos los usuarios con rol 'Encargado'
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

@receiver(post_save, sender=Bitacora)
def recalcular_riesgo_ia_automatico(sender, instance, created, **kwargs):
    """
    Cada vez que se crea o modifica una Bitácora, 
    la Inteligencia Artificial recalcula el riesgo del estudiante en tiempo real.
    """
    if created: # Solo recalcular si es una bitácora nueva
        try:
            predictor = PredictorRiesgo()
            
            # 1. Obtener al estudiante asociado a esta bitácora
            estudiante = instance.estudiante
            
            # 2. Pedirle a la IA el nuevo pronóstico
            nuevo_riesgo = predictor.predecir_estudiante(estudiante)
            
            # 3. Si el riesgo cambió, lo actualizamos silenciosamente
            if estudiante.nivel_riesgo_ia != nuevo_riesgo:
                estudiante.nivel_riesgo_ia = nuevo_riesgo
                # Usamos update_fields para no disparar otras señales y ser eficientes
                estudiante.save(update_fields=['nivel_riesgo_ia'])
                print(f"🤖 IA actualizó el riesgo de {estudiante.rut} a Nivel {nuevo_riesgo}")
                
        except Exception as e:
            print(f"❌ Error en cálculo automático de IA: {e}")


@receiver(post_delete, sender=Bitacora)
def recalcular_riesgo_ia_al_borrar(sender, instance, **kwargs):
    """ Si se borra una bitácora, la IA debe reevaluar el caso sin esa evidencia. """
    try:
        predictor = PredictorRiesgo()
        estudiante = instance.estudiante
        nuevo_riesgo = predictor.predecir_estudiante(estudiante)
        
        if estudiante.nivel_riesgo_ia != nuevo_riesgo:
            estudiante.nivel_riesgo_ia = nuevo_riesgo
            estudiante.save(update_fields=['nivel_riesgo_ia'])
            print(f"🤖 IA recalculó riesgo por eliminación de bitácora. Nivel actual: {nuevo_riesgo}")
    except Exception as e:
        print(f"❌ Error al recalcular IA por eliminación: {e}")

