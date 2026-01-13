from django.apps import AppConfig


class PublicacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.publicaciones"

    def ready(self):
        import apps.publicaciones.signals
