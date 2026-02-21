from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo de Usuario.
    Permite la creación de usuarios con campos adicionales como clave,
    nombres, apellidos, fecha de nacimiento, sexo, rol y carrera o puesto.

    Requiere:
        - Correo electrónico obligatorio.
        - Rol y carrera/puesto deben existir previamente en la base de datos.
    Si no se proporciona un rol, se asigna automáticamente el rol de 'paciente'.
    Returns:
        Usuario: Objeto de usuario creado y guardado en la base de datos.
    """

    def create_user(
        self,
        clave,
        nombres,
        email,
        apellido_paterno,
        fecha_nacimiento,
        sexo=None,
        apellido_materno=None,
        password=None,
        role=None,
        carrera_o_puesto=None,
    ):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")

        # if not password or len(password) < 8:
        #     raise ValueError('La contraseña debe tener al menos 8 caracteres')

        # Asignar el rol por defecto si no se proporciona uno
        if role is None:
            # role = Role.objects.get(nombre_rol='paciente')
            area_nombre = carrera_o_puesto
            if area_nombre == "Médico":
                role = Role.objects.get(nombre_rol="medico")
            # if area_nombre == 'ADMINISTRATIVO':
            #     role = Role.objects.get(nombre_rol='administrador')
            else:
                role = Role.objects.get(nombre_rol="paciente")

        # Buscar role y carrera
        try:
            role_obj = Role.objects.get(nombre_rol=role)
        except ObjectDoesNotExist:
            raise ValueError(f"El rol {role} no existe")

        # Buscar objeto de área correspondiente en la base de datos
        try:
            carrera_o_puesto_obj = Area.objects.get(carrera_o_puesto=carrera_o_puesto)
        except ObjectDoesNotExist:
            raise ValueError(f"La carrera o puesto {carrera_o_puesto} no existe")

        # Crear instancia de usuario con los datos proporcionados
        usuario = self.model(
            clave=clave,
            nombres=nombres,
            email=self.normalize_email(email),
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            role=role_obj,
            carrera_o_puesto=carrera_o_puesto_obj,
        )
        usuario.set_password(password)  # Hashea la contraseña
        usuario.save(using=self._db)

        return usuario

    """
    Crea y retorna un superusuario para el sistema.
    Este método extiende el método `create_user`, agregando los privilegios
    de superusuario y staff necesarios para acceder al panel de administración
    de Django.

    Returns:
        Usuario: Objeto de superusuario creado y guardado en la base de datos.
    """

    def create_superuser(
        self,
        clave,
        nombres,
        email,
        apellido_paterno=None,
        apellido_materno=None,
        fecha_nacimiento=None,
        sexo=None,
        password=None,
        role="paciente",
        carrera_o_puesto="ADMINISTRATIVO",
    ):
        usuario = self.create_user(
            clave=clave,
            nombres=nombres,
            email=email,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            password=password,
            role=role,
            carrera_o_puesto=carrera_o_puesto,
        )
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario


class Area(models.Model):
    """
    Modelo que representa las áreas académicas o puestos administrativos.
    Cada área o puesto está representado por una cadena única. Este modelo
    se utiliza para asociar a los usuarios con su carrera o función dentro
    de la institución.

    Atributos:
        carrera_o_puesto (CharField): Nombre único del área o puesto. Actúa como clave primaria.
    Métodos:
        __str__(): Retorna una representación legible del área o puesto.
    """

    carrera_o_puesto = models.CharField(max_length=50, unique=True, primary_key=True)

    def __str__(self):
        return self.carrera_o_puesto


class Role(models.Model):
    """
    Modelo que representa los roles que un usuario puede tener dentro del sistema.
    Cada rol define el nivel de acceso y funcionalidades disponibles
    para el usuario (ej. paciente, médico, administrador).

    Atributos:
        nombre_rol (CharField): Nombre único del rol. Actúa como clave primaria.
        descripcion (CharField): Descripción opcional del rol.
    Métodos:
        __str__(): Retorna una representación legible del rol.
    """

    nombre_rol = models.CharField(max_length=20, unique=True, primary_key=True)
    descripcion = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nombre_rol


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado de usuario para el sistema de gestión médica.
    Este modelo extiende `AbstractBaseUser` y `PermissionsMixin` para soportar
    autenticación personalizada mediante una clave única institucional y correo
    validado. Incluye campos para datos personales y de control de acceso.

    Métodos:
        (Heredados de `AbstractBaseUser` y `PermissionsMixin`)
    Requiere definir:
        - USERNAME_FIELD
        - REQUIRED_FIELDS
    """

    clave = models.CharField(
        "clave",
        max_length=9,
        primary_key=True,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^((AM|BIE|BIS|BLG|BII|BIM|BIB|CLG|CIM|CIE|CII|CIB|IB|IE|II|IM|ISC|LG|MI|MXI|MXM|MXE|MXS|MIA)[0-9]{4,6})|^(admin[0-9])|^([0-9]{4,6})$",
                message="Formato de clave no valido",
            )
        ],
    )
    email = models.EmailField(
        "Correo",
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^(?:(?:(?:am|bie|bis|blg|bii|bim|clg|cim|cie|cii|cib|ib|ie|ii|im|isc|lg|mi|mxi|mxm|mxe|mxs|mia)\d{6}|\d{4,6}|[A-Za-z]+(?:\.[A-Za-z]+))@itsatlixco\.edu\.mx|admin\d@admin\.com)$",
                message="Formato de correo no valido",
            )
        ],
    )
    nombres = models.CharField(
        "Nombres",
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^([A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ]+)( [A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ]+)?( [A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ]+)?$",
                message="El nombre debe ser en mayúsculas y no contener números",
            )
        ],
    )
    apellido_paterno = models.CharField(
        "Apellido Paterno",
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^[A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ]+",
                message="El apellido paterno debe ser en mayúsculas",
            )
        ],
    )
    apellido_materno = models.CharField(
        "Apellido Materno",
        max_length=30,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ]+",
                message="El apellido materno debe ser en mayúsculas",
            )
        ],
    )
    fecha_nacimiento = models.DateField("Fecha de Nacimiento", blank=True, null=True)
    sexos = [("M", "Masculino"), ("F", "Femenino")]
    sexo = models.CharField("Sexo", max_length=1, choices=sexos, blank=True, null=True)
    is_active = models.BooleanField("Usuario activo", default=True)
    is_staff = models.BooleanField(default=False)

    carrera_o_puesto = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "clave"
    REQUIRED_FIELDS = [
        "email",
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        "fecha_nacimiento",
    ]

    password = models.CharField("Contraseña", max_length=128, blank=True)

    def save(self, *args, **kwargs):
        """Sobrescribe el método save() para garantizar que la contraseña se guarde cifrada."""
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.password = make_password(self.password)

        if not self.pk and not self.has_usable_password():
            self.set_password(settings.DEFAULT_PASSWORD)

        if self.role is None:
            self.role = Role.objects.get(nombre_rol="paciente")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.clave} - {self.nombres} {self.apellido_paterno} {self.apellido_materno}"  # datos que se muestran en consultas e historiales

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True


class HistorialMedico(models.Model):
    """
    Modelo que representa el historial médico de un paciente.
    Contiene información relevante sobre condiciones crónicas, uso de sustancias,
    hábitos y otros factores clínicos. Cada historial está vinculado
    uno a uno con un paciente del sistema.

    Métodos:
        __str__(): Devuelve una representación en texto del identificador del historial.
    """

    id_historial = models.CharField(
        "Id Historial", max_length=9, primary_key=True, unique=True, editable=False
    )
    enfermedades_cronicas = models.CharField(
        "Enfermedades crónicas", max_length=150, blank=True, null=True
    )
    alergias = models.CharField("Alergias", max_length=150, blank=True, null=True)
    medicamento_usado = models.CharField(
        "Medicamento usado", max_length=150, blank=True, null=True
    )
    es_embarazada = models.BooleanField(default=False)
    usa_drogas = models.BooleanField(default=False)
    usa_cigarro = models.BooleanField(default=False)
    ingiere_alcohol = models.BooleanField(default=False)
    usa_lentes = models.BooleanField(default=False)
    vida_sexual_activa = models.BooleanField(default=False)
    usa_metodos_anticonceptivos = models.BooleanField(
        "Usa métodos anticonceptivos", default=False
    )

    paciente = models.OneToOneField(
        "Usuario",
        on_delete=models.CASCADE,
        related_name="historial",
        null=True,
        editable=False,
    )

    def __str__(self):
        return f"{self.id_historial}"


class ContactoEmergencia(models.Model):
    paciente = models.ForeignKey(
        "Usuario", on_delete=models.CASCADE, related_name="contactos_emergencia"
    )
    nombre = models.CharField("Nombre Completo", max_length=120)
    parentesco = models.CharField("Parentesco", max_length=50)
    telefono = models.CharField(
        "Teléfono",
        max_length=15,
        validators=[RegexValidator(r"^\+?\d{7,15}$", "Ingresa un teléfono válido.")],
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Evita duplicar el mismo número para un mismo paciente
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "telefono"], name="unique_telefono_por_paciente"
            )
        ]
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} ({self.parentesco}) - {self.telefono}"
