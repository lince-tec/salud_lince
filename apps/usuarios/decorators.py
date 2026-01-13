from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if (
                request.user.is_authenticated
                and request.user.role.nombre_rol in allowed_roles
            ):
                return view_func(request, *args, **kwargs)
            # return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
            return redirect("404.html")

        return _wrapped_view

    return decorator
