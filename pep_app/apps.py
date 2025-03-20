from django.apps import AppConfig

class PepAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pep_app'

    def ready(self):
        import pep_app.signals