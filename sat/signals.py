from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Bitacora, Notificacion, Usuario, Rol, Estudiante, HistorialRiesgo


@receiver(post_save, sender=Bitacora)
def notificar_observacion(sender, instance, created, **kwargs):
    if created:
        autor = instance.autor
        estudiante = instance.estudiante

        # Solo notificar si el estudiante tiene riesgo Medio (2) o Alto (3/4)
        nivel_riesgo = estudiante.nivel_riesgo_ia
        if nivel_riesgo < 1:
            return

        # Si el autor es Tutor, notificar a los Encargados y Superusuarios
        if autor and autor.rol.nombre == 'Tutor':
            encargados = Usuario.objects.filter(
                Q(rol__nombre='Encargado de Carrera') | 
                Q(email__in=User.objects.filter(is_superuser=True).values_list('email', flat=True))
            )
            observacion_texto = instance.observacion if instance.observacion else "Sin detalle"
            mensaje = f"📝 {observacion_texto}"

            for encargado in encargados:
                Notificacion.objects.create(
                    destinatario=encargado,
                    actor=autor,
                    mensaje=mensaje,
                    estudiante_relacionado=estudiante
                )


# ─────────────────────────────────────────────────────────────────────────────
# SEÑALES ML DE BITÁCORA DESACTIVADAS (cuello de botella de ~15s)
# Se reemplaza por el batch nocturno: recalcular_riesgos_batch
# ─────────────────────────────────────────────────────────────────────────────

# @receiver(post_save, sender=Bitacora)
# def recalcular_riesgo_ia_automatico(sender, instance, created, **kwargs):
#     DESACTIVADO: genera un delay de ~15s. Reemplazado por batch nocturno.


# ─────────────────────────────────────────────────────────────────────────────
# SEÑAL: Historial de cambios de riesgo en Estudiante
# ─────────────────────────────────────────────────────────────────────────────

@receiver(pre_save, sender=Estudiante)
def registrar_historial_riesgo(sender, instance, **kwargs):
    """
    Antes de guardar un Estudiante, si nivel_riesgo_ia cambia, registra en HistorialRiesgo.
    Detecta el origen: 'ML' (batch/recálculo IA) o 'HU' (corrección del EC).
    """
    if not instance.pk:
        return

    try:
        estudiante_anterior = Estudiante.objects.get(pk=instance.pk)
    except Estudiante.DoesNotExist:
        return

    # ── Detectar cambio en nivel_riesgo_ia ─────────────────────────────────
    if instance.nivel_riesgo_ia != estudiante_anterior.nivel_riesgo_ia:
        # Determinar origen: si riesgo_sobrescrito=True en el nuevo → fue el EC
        origen = 'HU' if (instance.riesgo_sobrescrito and not estudiante_anterior.riesgo_sobrescrito) else 'ML'
        HistorialRiesgo.objects.create(
            estudiante=instance,
            riesgo_anterior=estudiante_anterior.nivel_riesgo_ia,
            riesgo_nuevo=instance.nivel_riesgo_ia,
            origen_cambio=origen,
            usuario=instance.riesgo_corregido_por if origen == 'HU' else None
        )

    # ── Detectar cambio en nivel_riesgo_manual (etiqueta de reentrenamiento) ─
    manual_anterior = estudiante_anterior.nivel_riesgo_manual
    manual_nuevo = instance.nivel_riesgo_manual

    if manual_nuevo is not None and manual_nuevo != manual_anterior and instance.nivel_riesgo_ia == manual_nuevo:
        # El EC ya corrigió nivel_riesgo_ia arriba; no duplicar el historial.
        # Solo crear entradas separadas si el manual difiere del IA (caso raro de edición directa DB)
        pass


# ─────────────────────────────────────────────────────────────────────────────
# SEÑAL HITL: Notificar a EC cuando hay predicciones pendientes de validación
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Estudiante)
def notificar_prediccion_pendiente(sender, instance, **kwargs):
    """
    Cuando la IA cambia el riesgo de un estudiante y queda pendiente de validación,
    envía una notificación a todos los Encargados de Carrera.

    Evita duplicados: si ya existe una notificación no leída para este estudiante
    con el mismo mensaje, no crea otra.
    """
    if not instance.riesgo_pendiente_validacion:
        return

    nivel_nombre = {
        -1: 'Sin Contacto', 0: 'Sin Riesgo', 1: 'Bajo', 2: 'Medio', 3: 'Alto'
    }.get(instance.nivel_riesgo_ia, '?')

    mensaje = (
        f"🤖 Validación pendiente: {instance.nombre} {instance.apellido} "
        f"— IA predijo nivel \"{nivel_nombre}\". Confirmar o corregir."
    )

    # Notificar a Encargados de Carrera y también a Superusuarios
    encargados = Usuario.objects.filter(
        Q(rol__nombre='Encargado de Carrera') | 
        Q(email__in=User.objects.filter(is_superuser=True).values_list('email', flat=True))
    ).distinct()

    for encargado in encargados:
        # Evitar notificaciones duplicadas: si ya hay una no leída para este estudiante, omitir
        ya_existe = Notificacion.objects.filter(
            destinatario=encargado,
            estudiante_relacionado=instance,
            leida=False,
            mensaje__startswith="🤖 Validación pendiente:"
        ).exists()

        if not ya_existe:
            Notificacion.objects.create(
                destinatario=encargado,
                actor=None,
                mensaje=mensaje,
                estudiante_relacionado=instance
            )
