from .models import Notificacion, Usuario

def notificaciones_usuario(request):
    if request.user.is_authenticated:
        try:
            # Buscar el perfil SAT del usuario actual
            perfil = Usuario.objects.get(email=request.user.email)
            
            # Traemos las NO leídas del Usuario SAT
            notis = Notificacion.objects.filter(destinatario=perfil, leida=False)[:5]
            conteo = Notificacion.objects.filter(destinatario=perfil, leida=False).count()
            
            return {
                'mis_notificaciones': notis,
                'conteo_notificaciones': conteo
            }
        except Usuario.DoesNotExist:
            # Si no tiene perfil SAT, no mostrar notificaciones
            return {
                'mis_notificaciones': [],
                'conteo_notificaciones': 0
            }
    return {
        'mis_notificaciones': [],
        'conteo_notificaciones': 0
    }