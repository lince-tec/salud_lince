from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import Consulta, SignosVitales, CategoriaPadecimiento


# @receiver(post_save, sender=Consulta)
# def crear_signos_vitales(sender, instance, created, **kwargs):
#     '''Crea un SignosVitales cuando se crea una Consulta'''
#     if created:
#         SignosVitales.objects.create(consulta=instance)


# Usamos el decorador @receiver para escuchar la señal 'post_migrate', que se ejecuta después de que se apliquen las migraciones
@receiver(post_migrate)
def crear_motivos_de_consultas(sender, **kwargs):
    """
    Esta función se ejecuta automáticamente después de las migraciones para crear los motivos de consulta
    predefinidos en la base de datos. Los motivos se definen como categorías de padecimientos comunes que
    los pacientes podrían tener al visitar a un médico.
    """

    # Lista de padecimientos o motivos comunes de consulta
    padecimientos = [
        "IRAS",  # Infecciones respiratorias agudas
        "GASTROINTESTINALES",  # Problemas gastrointestinales
        "CONTROL PRENATAL",  # Control de embarazo
        "CEFALEA",  # Dolores de cabeza
        "QUEMADURAS",
        "LESIONES/HERIDAS",
        "MORDEDURA DE PERRO",
        "OTROS",  # Otros padecimientos no especificados
        "HIPERTENSIÓN",
        "DIABETES MELLITUS",
        "OBESIDAD",
        "ALERGIAS",
        "CARDIOVASCULARES",
        "NEUROLÓGICOS",
        "ANSIEDAD",
        "GINECOLÓGICO",  # Problemas ginecológicos
        "OFTALMICO",  # Problemas de visión
        "MUSCULOESQUELETICO",
        "SINCOPE",  # Desmayos o pérdida temporal de la conciencia
        "ASESORÍA",  # Consultas para orientación general
    ]

    # Iterar sobre la lista de padecimientos y crear una categoría de padecimiento para cada uno
    for padecimientoC in padecimientos:
        # Crear o buscar una categoría de padecimiento en la base de datos
        CategoriaPadecimiento.objects.get_or_create(padecimiento=padecimientoC)
