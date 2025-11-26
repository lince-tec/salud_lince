from datetime import datetime

from admin_extra_buttons.api import ExtraButtonsMixin, button
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
import pandas as pd

from .forms import BulkUserUploadForm, ValidarForm
from .models import Area, HistorialMedico, Role, Usuario, ContactoEmergencia
from django.contrib.admin import AdminSite
from django.conf import settings
import re


class SitioAdminSoloSuperusuarios(AdminSite):
    """
    Sitio de administración personalizado que restringe el acceso
    exclusivamente a usuarios superusuarios.
    Esta clase hereda de `AdminSite` y sobrescribe el método `has_permission`
    para permitir el ingreso solo a usuarios que estén activos y tengan el
    atributo `is_superuser` en `True`.

    Métodos:
        has_permission(request): Retorna True solo si el usuario es superusuario activo.
    """
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

admin_site = SitioAdminSoloSuperusuarios(name='miadmin')

class ContactoEmergenciaLine(admin.TabularInline):
    model = ContactoEmergencia
    extra = 0
    fields = ('nombre', 'parentesco', 'telefono')
    readonly_fields = ('creado',)

class UsuarioAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """
    Configuración personalizada del modelo Usuario para el sitio de administración.
    Esta clase define cómo se muestran, ordenan, filtran y buscan los usuarios
    dentro del panel de Django Admin. Además, agrega soporte para:
    - Encriptar la contraseña al guardar un nuevo usuario.
    - Incluir una URL personalizada para carga masiva de usuarios.
    """
    model = Usuario
    list_display = ('clave', 'nombres', 'role', 'is_staff') #Campos mostrados en la lista de registros.
    ordering = ('email',) #Orden predeterminado de los registros.
    list_filter = ('role', 'is_staff') #Filtros disponibles en la barra lateral.
    search_fields = ('clave', 'email', 'nombres',) #Campos que pueden ser buscados desde el buscador.
    form = ValidarForm  #vincula el formulario de las validaciones de fechas, claves, carreras y rol
    
    inlines = [ContactoEmergenciaLine]

    def save_model(self, request, obj, form, change):
        if not change:
            # Si no se proporciona una contraseña, se asigna una por defecto
            password = form.cleaned_data.get('password')
            if not password:
                password = settings.DEFAULT_PASSWORD  # Cambia esto por la contraseña que desees
            obj.set_password(password)

        super().save_model(request, obj, form, change)

    def get_urls(self):
        """
        Agrega una URL personalizada para la carga masiva de usuarios.
        Esta URL será accesible desde la interfaz de administración.

        -Sobrescribe el método get_urls() para agregar la URL personalizada."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk_upload", self.admin_site.admin_view(self.bulk_upload), name="bulk_upload"),
        ]
        return custom_urls + urls

    @button(label="Carga Masiva de Usuarios", html_attrs={"style": "background-color:#417690; color:white;"})
    def bulk_upload(self, request):
        """
        Vista personalizada para la carga masiva de usuarios desde un archivo CSV o Excel.

        - Lee el archivo con pandas.
        - Crea usuarios nuevos con bulk_create en lotes.
        - Actualiza usuarios existentes con bulk_update en lotes.
        - Devuelve mensajes claros de cuántos se crearon y cuántos se actualizaron.
        """
        if request.method == "POST":
            form = BulkUserUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES["file"]
                try:
                    # Leer archivo
                    if file.name.endswith(".csv"):
                        df = pd.read_csv(file, dtype=str)
                    elif file.name.endswith((".xls", ".xlsx")):
                        df = pd.read_excel(file, dtype=str)
                    else:
                        messages.error(request, "Formato de archivo no compatible.")
                        return redirect("..")

                    usuarios_nuevos = []
                    usuarios_existentes = []

                    # Obtener claves de usuarios ya registrados
                    claves_existentes = set(Usuario.objects.values_list("clave", flat=True))

                    for index, row in df.iterrows():
                        try:
                            # Validar valores vacíos y corregir tipos de datos
                            apellido_materno = str(row.get("apellido_materno", "")).strip() or None
                            valor_pas = row.get("password", "")
                            pas = settings.DEFAULT_PASSWORD if pd.isna(valor_pas) or str(valor_pas).strip() == "" else str(valor_pas).strip()

                            # Validar contraseña
                            token_password = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%#?&ñ_])[A-Za-z\d@$!%#?&ñ_]{8,15}$'
                            if not re.match(token_password, pas):
                                messages.error(request, f"Fila {index + 1}: La contraseña no cumple con el formato.")
                                continue

                            # Obtener área y rol
                            area_obj = Area.objects.get(carrera_o_puesto=row.get("carrera_o_puesto"))
                            area_nombre = area_obj.carrera_o_puesto.strip()
                            role_obj = Role.objects.get(nombre_rol="medico" if area_nombre == "Médico" else "paciente")

                            # Convertir fecha de nacimiento
                            fecha_nacimiento = None
                            if row.get("fecha_nacimiento"):
                                fecha_nacimiento = datetime.strptime(
                                    str(row["fecha_nacimiento"]), "%d/%m/%Y"
                                ).strftime("%Y-%m-%d")

                            usuario = Usuario(
                                clave=row["clave"],
                                email=row["email"],
                                nombres=row["nombres"],
                                apellido_paterno=row["apellido_paterno"],
                                apellido_materno=apellido_materno,
                                fecha_nacimiento=fecha_nacimiento,
                                sexo=row.get("sexo", None),
                                is_active=True,
                                is_staff=row.get("is_staff", "False") == "True",
                                carrera_o_puesto_id=row.get("carrera_o_puesto", None),
                                role_id=role_obj.nombre_rol,
                            )

                            if row["clave"] in claves_existentes:
                                usuarios_existentes.append(usuario)
                            else:
                                usuario.set_password(pas)
                                usuarios_nuevos.append(usuario)

                        except Exception as e:
                            messages.error(request, f"Error en la fila {index + 1}: {e}")

                    # Inserción y actualización en lotes
                    if usuarios_nuevos:
                        # Guardar los usuarios creados
                        usuarios_creados = Usuario.objects.bulk_create(usuarios_nuevos, batch_size=100)

                        # Crear historiales médicos para los nuevos pacientes
                        from django.contrib.auth.models import Group
                        from .models import HistorialMedico

                        for usuario in usuarios_creados:
                            # Verificar si es un paciente que necesita historial
                            if (hasattr(usuario, 'role') and
                                hasattr(usuario.role, 'nombre_rol') and
                                usuario.role.nombre_rol.lower() == 'paciente' and
                                hasattr(usuario, 'carrera_o_puesto') and
                                usuario.carrera_o_puesto != 'Médico'):

                                HistorialMedico.objects.get_or_create(
                                    id_historial=usuario.clave,
                                    defaults={'paciente': usuario}
                                )

                            # Asignar grupo correspondiente
                            if hasattr(usuario, 'role') and hasattr(usuario.role, 'nombre_rol'):
                                group_name = usuario.role.nombre_rol.capitalize()
                                try:
                                    group = Group.objects.get(name=group_name)
                                    usuario.groups.add(group)
                                except Group.DoesNotExist:
                                    pass

                    if usuarios_existentes:
                        Usuario.objects.bulk_update(
                            usuarios_existentes,
                            [
                                "email", "nombres", "apellido_paterno", "apellido_materno",
                                "fecha_nacimiento", "sexo", "is_active", "is_staff",
                                "carrera_o_puesto_id", "role_id"
                            ],
                            batch_size=100
                        )

                    messages.success(
                        request,
                        f"Usuarios creados: {len(usuarios_nuevos)}, actualizados: {len(usuarios_existentes)}."
                    )
                    return redirect("..")

                except Exception as e:
                    messages.error(request, f"Ocurrió un error: {e}")
                    return redirect("..")
        else:
            form = BulkUserUploadForm()

        return render(request, "admin_custom/bulk_upload.html", {"form": form, "opts": self.model._meta})


class HistorialAdmin(admin.ModelAdmin):
    """
    Configuración personalizada para el modelo HistorialMedico en el panel de administración.

    Esta clase define cómo se presentan los historiales médicos en la interfaz de Django Admin,
    permitiendo una vista rápida de los principales campos clínicos y el uso de filtros y búsqueda.
    """
    model = HistorialMedico
    list_display = ('id_historial', 'enfermedades_cronicas', 'alergias', 'medicamento_usado', 'es_embarazada', 'usa_drogas', 'usa_cigarro', 'ingiere_alcohol')
    ordering = ('id_historial',)
    list_filter = ('es_embarazada', 'usa_drogas', 'usa_cigarro', 'ingiere_alcohol')
    search_fields = ('id_historial',)


class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ('nombre_rol', 'descripcion')
    ordering = ('nombre_rol',)
    list_filter = ('nombre_rol',)

class AreaAdmin(admin.ModelAdmin):
    model = Area
    list_display = ('carrera_o_puesto',)
    ordering = ('carrera_o_puesto',)
    list_filter = ('carrera_o_puesto',)

class ContactoEmergenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'parentesco', 'telefono', 'paciente', 'creado')
    search_fields = ('nombre', 'telefono', 'paciente__clave', 'paciente__nombres')
    list_filter = ('parentesco',)
    ordering = ('-creado',)


admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(HistorialMedico, HistorialAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(ContactoEmergencia, ContactoEmergenciaAdmin)