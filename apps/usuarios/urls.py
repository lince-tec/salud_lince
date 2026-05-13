from django.urls import path
from apps.usuarios import views

from django.contrib.auth import views as auth_views
from apps.usuarios.forms import RecuperarPasswordForm

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("medico/dashboard/", views.medico_dashboard_view, name="medico_dashboard"),
    path("paciente/dashboard/", views.paciente_dashboard_view, name="paciente_dashboard"),
    path("paciente/historial/", views.historial_view, name="historial"),
    path( "paciente/mis_consultas/", views.paciente_consultas_view, name="paciente_consultas",),
    path("cambiar_contrasena/", views.cambiar_contrasena_view, name="cambiar_contrasena"),
    path("informacion/", views.usuario_informacion_view, name="informacion"),
    path("guardar-contacto/", views.guardar_contactos_view, name="guardar_contactos"),

    path("medico/consultas/", views.medico_consultas_view, name="medico_consultas"),
    path("medico/historiales/", views.medico_historiales_view, name="medico_historiales"),
    path( "medico/editar_historial/<str:pk>/", views.editar_historial_view, name="editar_historial", ),

    path("recuperar/", auth_views.PasswordResetView.as_view(template_name="contrasena/recuperar_contrasena.html", email_template_name= "contrasena/email_recuperacion.html", form_class=RecuperarPasswordForm), name="password_reset",),
    path("recuperar/enviado", auth_views.PasswordResetDoneView.as_view(template_name="contrasena/recuperar_enviado.html"), name="password_reset_done",),
    path("recuperar/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="contrasena/confirmar_contrasena.html"), name="password_reset_confirm",),
    path("recuperar/completo", auth_views.PasswordResetCompleteView.as_view(template_name="contrasena/recuperacion_completa.html"), name="password_reset_complete",),


]
