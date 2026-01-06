from django.apps import AppConfig


class SatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sat'

    def ready(self):
        import sat.signals  # <--- ESTO ACTIVA LAS SEÑALES
