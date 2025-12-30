from django.apps import AppConfig

class DonacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donaciones'

    def ready(self):
        import donaciones.signals # Importante para activar las señales