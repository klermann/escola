from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'DIÁRIO DE CLASSE DIGITAL '

    def ready(self):
        import core.signals 

