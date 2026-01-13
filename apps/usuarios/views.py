import re

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


from apps.consultas.models import CategoriaPadecimiento, Consulta, SignosVitales

from apps.usuarios.decorators import role_required
from apps.usuarios.forms import HistorialMedicoForm
from apps.usuarios.forms import LoginForm
from apps.usuarios.models import Area, HistorialMedico, Usuario, ContactoEmergencia

from apps.usuarios.views_dashboard_utils import (
    generate_habitos_figure,
    generate_consultas_figure,
    generate_area_distribution_figure,
    generate_area_vs_padecimientos_figure,
    generate_gender_figures,
)

from apps.publicaciones.views import obtener_publicaciones


@never_cache
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@ratelimit(key="ip", rate="5/m", method="GET", block=True)
def login_view(request):
    """
    Vista para iniciar sesión de usuarios según su rol.

    Si el usuario ya está autenticado, lo redirige a su panel correspondiente.
    Si no, procesa el formulario de inicio de sesión (LoginForm).

    Returns:
        HttpResponse: Redirección al panel de usuario correspondiente o renderizado del formulario de login.
    """
    if request.user.is_authenticated:
        rol = request.user.role.nombre_rol
        if rol == "medico":
            return redirect("medico_dashboard")
        if rol == "paciente":
            return redirect("paciente_dashboard")
        # if rol == "admin":
        #     return redirect("/admin/")

        messages.error(request, "Rol no reconocido.")
        return redirect("login")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Formulario inválido.")
            return render(request, "login.html", {"form": form})

        clave = form.cleaned_data["clave"]
        password = form.cleaned_data["password"]
        user = authenticate(request, clave=clave, password=password)

        if user is None:
            messages.error(request, "Credenciales inválidas.")
            return render(request, "login.html", {"form": form})

        login(request, user)
        rol = user.role.nombre_rol
        if rol == "medico":
            return redirect("medico_dashboard")
        if rol == "paciente":
            return redirect("paciente_dashboard")
        # if rol == "admin":
        #     return redirect("/admin/")

        messages.error(request, "Rol no reconocido.")
        return redirect("login")

    form = LoginForm()
    return render(request, "login.html", {"form": form})


@never_cache
def logout_view(request):
    """
    vista desloguear al usuario

    Returns:
        HttpResponse: respuesta http dirigida a la vista de inicio de sesión
    """
    logout(request)
    return redirect("login")


@never_cache
@login_required
@role_required(["medico"])
def medico_dashboard_view(request):
    habitos_fig = generate_habitos_figure()
    consultas_fig = generate_consultas_figure()
    areas_fig = generate_area_distribution_figure()
    padecimientos_fig = generate_area_vs_padecimientos_figure()
    genero_fig, genero_pastel = generate_gender_figures()

    context = {
        "habitos_graph": habitos_fig.to_html(full_html=False),
        "consultas_graph": consultas_fig.to_html(full_html=False),
        "areas_graph": areas_fig.to_html(full_html=False),
        "padecimientos_graph": padecimientos_fig.to_html(full_html=False),
        "genero_graph": genero_fig.to_html(full_html=False),
        "genero_pastel": genero_pastel.to_html(full_html=False),
    }

    return render(request, "medico_dashboard.html", context)


@never_cache
@login_required
@role_required(["paciente"])
def paciente_dashboard_view(request):
    """
    Vista del panel principal para los pacientes.

    Requiere:
        - Que el usuario esté autenticado.
        - Que el usuario tenga el rol de 'paciente'.

    Returns:
        HttpResponse: Renderizado de la plantilla del dashboard del paciente.
    """
    glosario = [
        {
            "id": "alergia",
            "termino": "Alergia",
            "definicion": "Reacción del sistema inmunológico ante sustancias inofensivas para la mayoría.",
        },
        {
            "id": "antibiotico",
            "termino": "Antibiótico",
            "definicion": "Medicamento usado para tratar infecciones bacterianas.",
        },
        {
            "id": "asintomatico",
            "termino": "Asintomático",
            "definicion": "Persona que tiene una enfermedad pero no presenta síntomas visibles.",
        },
        {
            "id": "diabetes",
            "termino": "Diabetes",
            "definicion": "Enfermedad metabólica que se produce por niveles elevados de glucosa en sangre.",
        },
        {
            "id": "hipertension",
            "termino": "Hipertensión",
            "definicion": "Enfermedad crónica caracterizada por el aumento de la presión arterial.",
        },
        {
            "id": "vacuna",
            "termino": "Vacuna",
            "definicion": "Sustancia que estimula la producción de defensas para prevenir enfermedades.",
        },
    ]

    flashcards = [
        {
            "pregunta": "¿Cuál es una señal común de deshidratación?",
            "respuesta": "Boca seca, fatiga y orina de color oscuro.",
        },
        {
            "pregunta": "¿Qué es la hipertensión?",
            "respuesta": "Es una enfermedad crónica que afecta la presión arterial.",
        },
        {
            "pregunta": "¿Cuánto tiempo se recomienda dormir diariamente en promedio?",
            "respuesta": "Entre 7 y 9 horas por noche para un adulto.",
        },
        {
            "pregunta": "Verdadero o falso: La actividad física mejora el estado de ánimo.",
            "respuesta": "Verdadero. Libera endorfinas que ayudan a sentirse mejor.",
        },
        {
            "pregunta": "¿Cuántas veces al día se recomienda lavarse los dientes?",
            "respuesta": "Al menos dos veces al día, después de las comidas.",
        },
        {
            "pregunta": "¿Qué es el estrés?",
            "respuesta": "Una respuesta del cuerpo ante situaciones de presión o peligro.",
        },
    ]
    publicaciones = obtener_publicaciones()
    return render(
        request,
        "paciente_dashboard.html",
        {
            "glosario": glosario,
            "flashcards": flashcards,
            "publicaciones": publicaciones,
        },
    )


@never_cache
@ratelimit(key="ip", rate="5/m", method="GET", block=True)
@login_required
@role_required(["paciente"])
def historial_view(request):
    """
    Vista para mostrar el historial médico del paciente.

    Requiere:
        - Autenticación del usuario.
        - Que el usuario tenga el rol de 'paciente'.
        - No más de 5 solicitudes GET por minuto por IP.

    Returns:
        HttpResponse: Renderizado de la plantilla con el historial médico del paciente.
    """
    # obtener el historial médico del paciente
    historial = request.user.historial
    return render(request, "historial_medico.html", {"historial": historial})


@never_cache
@ratelimit(key="ip", rate="10/m", method="GET", block=True)
@login_required
@role_required(["paciente"])
def paciente_consultas_view(request):
    """
    Vista para mostrar las consultas médicas del paciente autenticado.

    Aplica paginación para mostrar un número limitado de consultas por página.
    """
    consultas = Consulta.objects.filter(clave_paciente=request.user).select_related(
        "signos_vitales"
    )

    paginador = Paginator(consultas, 20)  # Mostrar 10 consultas por páginas
    pagina = request.GET.get("page", 1)
    try:
        consultas = paginador.page(pagina)
    except PageNotAnInteger:
        consultas = paginador.page(1)
    except EmptyPage:
        consultas = paginador.page(paginador.num_pages)

    return render(request, "paciente_consultas.html", {"consultas": consultas})


@never_cache
@ratelimit(key="ip", rate="5/m", method="GET", block=True)
@login_required
@role_required(["paciente", "medico"])
def usuario_informacion_view(request):
    """
    Vista para mostrar la información básica del usuario autenticado.

    Esta vista es accesible tanto para pacientes como médicos.
    """
    informacion = request.user
    contactos = []

    if hasattr(request.user, "contactos_emergencia"):
        contactos = request.user.contactos_emergencia.all().order_by("id")

    return render(
        request,
        "informacion.html",
        {
            "informacion": informacion,
            "contactos": contactos,
        },
    )


@never_cache
@ratelimit(
    key="ip", rate="5/m", method="POST", block=True
)  # Limite 5 solicitudes POST por minuto por IP
@ratelimit(
    key="ip", rate="10/m", method="GET", block=True
)  # Limite 10 solicitudes GET por minuto por IP
@login_required
@role_required(["paciente", "medico"])
def cambiar_contrasena_view(request):
    """
    Vista que permite al usuario cambiar su contraseña.

    Solo es accesible para usuarios autenticados con los roles 'paciente' o 'medico'.
    La contraseña debe cumplir con ciertos requisitos de seguridad.
    """
    if request.method == "POST":  # Solo se ejecuta si la solicitud es de tipo POST
        # Obtención de las contraseñas ingresadas por el usuario desde el formulario
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        # Validación de la nueva contraseña con expresión regular (mínimo 8 y máximo 15 caracteres,
        # debe incluir al menos una letra mayúscula, un número y un carácter especial)
        if not re.match(
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,15}$",
            new_password,
        ):
            messages.error(request, "Contraseña inválida")
            return redirect("informacion")  # Redirige si no cumple con los requisitos

        # Validación para la confirmación de la nueva contraseña
        if not re.match(
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,15}$",
            confirm_password,
        ):
            messages.error(request, "Contraseña inválida")
            return redirect("informacion")  # Redirige si no cumple con los requisitos

        # Verificación de que la contraseña actual ingresada por el usuario sea correcta
        if not request.user.check_password(current_password):
            error_message = "La contraseña actual es incorrecta."
            return render(
                request,
                "informacion.html",
                {"informacion": request.user, "error": error_message},
            )

        # Verificación de que la nueva contraseña y la confirmación coincidan
        if new_password != confirm_password:
            error_message = "Las contraseñas no coinciden."
            return render(
                request,
                "informacion.html",
                {"informacion": request.user, "error": error_message},
            )

        # Si todo es correcto, se cambia la contraseña del usuario
        request.user.set_password(new_password)
        request.user.save()
        # Mantener la sesión activa después del cambio de contraseña
        update_session_auth_hash(request, request.user)
        messages.success(request, "Tu contraseña ha sido cambiada exitosamente.")
        return redirect("informacion")

    return redirect("informacion")


@never_cache
@ratelimit(
    key="ip", rate="10/m", method="GET", block=True
)  # Limite 10 solicitudes GET por minuto por IP
@login_required
@role_required(["medico"])
def medico_consultas_view(request):
    """
    Vista para que los médicos vean sus consultas o todas las consultas si así lo desean.

    Si el parámetro 'todas' está presente en la URL, se mostrarán todas las consultas.
    Si no, se mostrarán solo las consultas relacionadas con el médico autenticado.
    """
    mostrar_todas = request.GET.get("todas", "0") == "1"  # Leer parámetro 'todas'
    consultas_base = Consulta.objects.select_related(
        "clave_medico", "clave_paciente", "signos_vitales"
    )

    if not mostrar_todas:
        consultas_base = consultas_base.filter(clave_medico=request.user)

    clave_paciente_query = request.GET.get(
        "clave_paciente"
    )  # variables para la busqueda
    fecha_inicio_query = request.GET.get("fecha_inicio")
    fecha_fin_query = request.GET.get("fecha_fin")

    if clave_paciente_query:  # busqueda por clave del paciente
        consultas_base = consultas_base.filter(
            clave_paciente__clave__icontains=clave_paciente_query
        )

    if fecha_inicio_query and fecha_fin_query:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_query, "%Y-%m-%d")
            fecha_fin = datetime.strptime(fecha_fin_query, "%Y-%m-%d") + timedelta(
                days=1
            )
            consultas_base = consultas_base.filter(
                fecha__gte=fecha_inicio, fecha__lt=fecha_fin
            )
        except ValueError:
            pass
    elif fecha_inicio_query:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_query, "%Y-%m-%d")
            consultas_base = consultas_base.filter(fecha__gte=fecha_inicio)
        except ValueError:
            pass
    elif fecha_fin_query:
        try:
            fecha_fin_query = datetime.strptime(
                fecha_fin_query, "%Y-%m-%d"
            ) + timedelta(days=1)
            consultas_base = consultas_base.filter(fecha__lt=fecha_fin)
        except ValueError:
            pass

    consultas = consultas_base.order_by("-fecha")

    paginador = Paginator(consultas, 20)  # Mostrar 10 consultas por páginas
    pagina = request.GET.get("page", 1)
    try:
        consultas = paginador.page(pagina)
    except PageNotAnInteger:
        consultas = paginador.page(1)
    except EmptyPage:
        consultas = paginador.page(paginador.num_pages)

    return render(
        request,
        "medico_consultas.html",
        {
            "consultas": consultas,
            "mostrar_todas": mostrar_todas,
            "clave_paciente": clave_paciente_query,
            "fecha_inicio": fecha_inicio_query,
            "fecha_fin": fecha_fin_query,
        },
    )


@never_cache
@login_required
@role_required(["medico"])
def medico_historiales_view(request):
    """
    Vista para que los médicos vean los historiales médicos de los pacientes.

    Si se proporciona un parámetro de búsqueda, los historiales se filtrarán de acuerdo al ID del historial.
    También se paginan los resultados para mostrar solo una cantidad limitada por página.
    """
    query = request.GET.get("search", "")
    query = query.strip().upper()
    # Si hay una consulta, filtrar los historiales de acuerdo a la consulta
    if query:
        historiales = (
            HistorialMedico.objects.filter(
                id_historial__icontains=query,
                paciente__role__nombre_rol="paciente",
                paciente__is_active=True,
            )
            .exclude(paciente__carrera_o_puesto__carrera_o_puesto="Médico")
            .order_by("id_historial")
        )
    else:
        historiales = (
            HistorialMedico.objects.filter(
                paciente__role__nombre_rol="paciente", paciente__is_active=True
            )
            .exclude(paciente__carrera_o_puesto__carrera_o_puesto="Médico")
            .order_by("id_historial")
        )

    paginador = Paginator(historiales, 10)  # Mostrar 10 consultas por páginas
    pagina = request.GET.get("page", 1)
    try:
        historiales = paginador.page(pagina)
    except PageNotAnInteger:
        historiales = paginador.page(1)
    except EmptyPage:
        historiales = paginador.page(paginador.num_pages)

    return render(
        request, "medico_historiales.html", {"historiales": historiales, "query": query}
    )


@never_cache
@login_required
@role_required(["medico"])
def editar_historial_view(request, pk):
    """
    Vista que permite al médico editar un historial médico existente.

    Solo se permite a los médicos editar los historiales de los pacientes.
    Si la solicitud es de tipo POST, se guarda el formulario con los nuevos datos,
    de lo contrario, se muestra el formulario con los datos actuales del historial.
    """
    historial = get_object_or_404(HistorialMedico, id_historial=pk)
    datos = request.POST if request.method == "POST" else None
    form = HistorialMedicoForm(datos, instance=historial)
    paciente = historial.paciente

    contactos = ContactoEmergencia.objects.filter(paciente=paciente)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("medico_historiales")

    return render(
        request,
        "editar_historial.html",
        {"form": form, "historial": historial, "contactos": contactos},
    )


telefono_validator = RegexValidator(
    r"^\+?\d{7,15}$", "Ingresa un teléfono válido (7 a 15 dígitos, opcional +)."
)


@role_required(["paciente"])
def guardar_contactos_view(request):
    """
    Guarda o actualiza los contactos de emergencia de un paciente.
    """
    if request.method == "POST":
        paciente = request.user  # usuario autenticado

    p = request.user

    # 1) Leer datos
    c1 = {
        "nombre": request.POST.get("nombre_1", "").strip(),
        "parentesco": request.POST.get("parentesco_1", "").strip(),
        "telefono": request.POST.get("telefono_1", "").strip(),
    }
    c2 = {
        "nombre": request.POST.get("nombre_2", "").strip(),
        "parentesco": request.POST.get("parentesco_2", "").strip(),
        "telefono": request.POST.get("telefono_2", "").strip(),
    }

    # 2) Normalizar lista de contactos a guardar (solo los completos)
    contactos = []
    if all(c1.values()):
        contactos.append(c1)
    if all(c2.values()):
        contactos.append(c2)

    # Validación: debe haber al menos 1 contacto completo
    if not contactos:
        messages.error(
            request,
            "Debes completar al menos un contacto (nombre, parentesco y teléfono).",
        )
        return redirect("informacion")

    # Validación: máximo 2 (por si cambias el formulario luego)
    if len(contactos) > 2:
        messages.error(request, "Solo puedes registrar hasta dos contactos.")
        return redirect("informacion")

    # Validación: teléfonos válidos y distintos entre sí
    try:
        for c in contactos:
            telefono_validator(c["telefono"])
    except ValidationError as e:
        messages.error(request, f"Teléfono inválido: {e.message}")
        return redirect("informacion")

    telefonos = [c["telefono"] for c in contactos]
    if len(set(telefonos)) != len(telefonos):
        messages.error(request, "Los teléfonos de los contactos no pueden ser iguales.")
        return redirect("informacion")

    # 3) Guardar de forma atómica: borro anteriores y creo nuevos
    try:
        with transaction.atomic():
            ContactoEmergencia.objects.filter(paciente=p).delete()
            ContactoEmergencia.objects.bulk_create(
                [ContactoEmergencia(paciente=p, **c) for c in contactos]
            )
    except IntegrityError:
        # Por si acaso (colisión con otra sesión, etc.)
        messages.error(
            request, "Ya existe un contacto con ese teléfono para este paciente."
        )
        return redirect("informacion")

    messages.success(request, "Contactos de emergencia guardados correctamente.")
    return redirect("informacion")
