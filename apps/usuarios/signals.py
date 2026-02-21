from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from apps.consultas.models import Consulta

from .models import Area, HistorialMedico, Role, Usuario


@receiver(post_migrate)
def crear_roles_por_defecto(sender, **kwargs):
    """
    Esta función crea los roles por defecto en la base de datos después de que se haya realizado una migración.

    Los roles por defecto son: 'paciente', 'medico', y 'admin'.
    Si ya existen en la base de datos, no se crean nuevamente.
    """
    roles = ["paciente", "medico"]  # admin
    for role in roles:
        Role.objects.get_or_create(nombre_rol=role)


@receiver(post_migrate)
def crear_areas_por_defecto(sender, **kwargs):
    """
    Esta función crea áreas por defecto en la base de datos después de que se haya realizado una migración.

    Las áreas por defecto incluyen diferentes disciplinas y puestos relacionados con la institución.
    Si ya existen en la base de datos, no se crean nuevamente.
    """
    areas = [
        "ING. SISTEMAS COMP.",
        "ING. BIOQUÍMICA",
        "ING. MECATRÓNICA",
        "ING. INDUSTRIAL",
        "I. ELECTROMECÁNICA",
        "GASTRONOMÍA",
        "M. EN INGENIERÍA",
        "Médico",
        "ADMINISTRATIVO",
        "DOCENTE",
    ]
    for area in areas:
        Area.objects.get_or_create(carrera_o_puesto=area)


@receiver(post_migrate)
def crear_grupos_permisos(sender, **kwargs):
    """
    Esta función crea los grupos de usuarios y asigna los permisos correspondientes a cada uno después de una migración.

    Los grupos creados son: 'Medico', 'Paciente', y 'Administrador'.
    Además, se asignan permisos específicos a cada grupo según el modelo al que se refieren.
    """
    # Crear grupos si no existen
    medico_group, _ = Group.objects.get_or_create(
        name="Medico"
    )  # Crear el grupo 'Medico'
    paciente_group, _ = Group.objects.get_or_create(
        name="Paciente"
    )  # Crear el grupo 'Paciente'
    admin_group, _ = Group.objects.get_or_create(
        name="Administrador"
    )  # Crear el grupo 'Administrador'

    # Definir permisos y grupos
    permisos_medico = [
        ("view_consulta", Consulta),  # Permiso para ver consultas
        ("add_consulta", Consulta),  # Permiso para agregar consultas
        ("view_historialmedico", HistorialMedico),  # Permiso para ver historial médico
        ("view_usuario", Usuario),  # Permiso para ver usuarios
        ("change_usuario", Usuario),  # Permiso para cambiar usuarios
    ]
    permisos_paciente = [
        ("view_consulta", Consulta),  # Permiso para ver consultas
        ("view_historialmedico", HistorialMedico),  # Permiso para ver historial médico
        (
            "change_historialmedico",
            HistorialMedico,
        ),  # Permiso para cambiar historial médico
        ("view_usuario", Usuario),  # Permiso para ver usuarios
        ("change_usuario", Usuario),  # Permiso para cambiar usuarios
    ]

    # Asignar permisos a los grupos
    def asignar_permisos(grupo, permisos):
        for permiso_codename, model in permisos:
            content_type = ContentType.objects.get_for_model(model)
            permission, _ = Permission.objects.get_or_create(
                codename=permiso_codename, content_type=content_type
            )
            grupo.permissions.add(permission)

    # Asignar permisos a cada grupo
    asignar_permisos(medico_group, permisos_medico)
    asignar_permisos(paciente_group, permisos_paciente)

    # Asignar todos los permisos al grupo Administrador
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)


@receiver(post_save, sender=Usuario)
def asignar_grupo_y_crear_historial(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta automáticamente después de que se cree un nuevo usuario ('Usuario').

    Dependiendo del rol del usuario, se asigna a un grupo correspondiente (Medico, Paciente, Administrador).
    Si el rol es 'paciente', también se crea un historial médico para el paciente si corresponde.
    """
    # Verificar si el usuario ha sido creado (no actualizado)
    if created:
        # Si el usuario es un médico, asignarlo al grupo 'Medico'
        if instance.role == Role.objects.get(nombre_rol="medico"):
            medico_group = Group.objects.get(name="Medico")
            instance.groups.add(medico_group)

        # Si el usuario es un paciente, asignarlo al grupo 'Paciente' y crear un historial médico
        elif instance.role == Role.objects.get(nombre_rol="paciente"):
            paciente_group = Group.objects.get(name="Paciente")
            instance.groups.add(paciente_group)
            # Si el paciente tiene una carrera o puesto (y no es médico), crear su historial médico
            if instance.carrera_o_puesto and instance.carrera_o_puesto != "Médico":
                HistorialMedico.objects.create(
                    id_historial=instance.clave, paciente=instance
                )

        # Si el usuario es un administrador, asignarlo al grupo 'Administrador'
        # elif instance.role == Role.objects.get(nombre_rol='admin'):
        #     admin_group = Group.objects.get(name='Administrador')
        #     instance.groups.add(admin_group)
        # Guardar el usuario con los cambios de grupo
        instance.save()
