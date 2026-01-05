from django import template
from sat.models import Usuario

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_perfil(email):
    """Obtiene el perfil de Usuario por email"""
    try:
        return Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return None