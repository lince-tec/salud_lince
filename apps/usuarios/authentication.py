from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class ClaveBackend(ModelBackend):
    def authenticate(self, request, clave=None, password=None, **kwargs):
        Usuario = get_user_model()
        try:
            user = Usuario.objects.get(clave=clave)
            if user.check_password(password):
                return user
        except Usuario.DoesNotExist:
            return None
