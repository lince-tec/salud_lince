from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def redirigir_admin_login(request):
    return redirect("login")  # Asegúrate que la vista de login tenga el name="login"

urlpatterns = [
    path('admin/login/', redirigir_admin_login),  # ⬅️ Esta línea debe ir antes que 'admin/'
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('consultas/', include('apps.consultas.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('lincybot/', include('chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
