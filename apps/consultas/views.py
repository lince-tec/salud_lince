from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.usuarios.decorators import role_required
from apps.usuarios.models import Usuario

from .forms import ConsultaForm, SignosVitalesForm

import pandas as pd
from django.http import HttpResponse
from .models import Consulta
from datetime import datetime


@never_cache
@login_required
@role_required(["medico"])
def crear_consulta_view(request):
    """
    Vista para crear una nueva consulta médica y registrar los signos vitales del paciente.
    Solo accesible para usuarios con el rol de 'medico'.
    """
    # Verificar si el usuario tiene el rol 'medico'. Si no, redirigir al dashboard con un mensaje de error.
    if not request.user.role.nombre_rol == "medico":
        messages.error(request, "Solo los médicos pueden crear consultas.")
        return redirect("dashboard")
    # Crear las instancias de los formularios con los datos enviados
    consulta_form = ConsultaForm(data=request.POST or None)
    signos_form = SignosVitalesForm(data=request.POST or None)

    # Si el método es POST (es decir, el usuario está enviando el formulario)
    if request.method == "POST":
        # Validar ambos formularios
        if consulta_form.is_valid() and signos_form.is_valid():
            clave = request.POST.get("clave_paciente_display").split("-")[0].strip()
            try:
                paciente = Usuario.objects.get(
                    clave=clave, role__nombre_rol="paciente", is_active=True
                )
            except Usuario.DoesNotExist:
                messages.error(request, "No se encontró un paciente con esa clave.")
                return redirect("crear_consulta")

            consulta = consulta_form.save(commit=False)
            consulta.clave_medico = request.user
            consulta.clave_paciente = paciente
            consulta.save()

            signos_vitales = signos_form.save(commit=False)
            signos_vitales.consulta = consulta
            if (
                signos_vitales.peso
                and signos_vitales.talla
                and signos_vitales.talla > 0
            ):  # Formula para calcular el imc
                signos_vitales.imc = round(
                    signos_vitales.peso / (signos_vitales.talla**2), 2
                )
            else:
                signos_vitales.imc = None
            signos_vitales.save()

            messages.success(request, "Consulta registrada correctamente.")
            return redirect("medico_consultas")
        else:
            # Si los formularios no son válidos, mostrar un mensaje de error
            messages.error(request, "Por favor corrige los errores en el formulario.")
    # Si el método no es POST, solo mostrar los formularios vacíos

    # Renderizar la plantilla con los formularios
    return render(
        request,
        "crear_consulta.html",
        {"consulta_form": consulta_form, "signos_form": signos_form},
    )


@csrf_exempt
@never_cache
@login_required
@role_required(["medico"])
def buscar_paciente_por_clave_view(request):
    clave = request.GET.get("clave", "").lower()
    try:
        paciente = Usuario.objects.get(
            clave__iexact=clave, role__nombre_rol="paciente", is_active=True
        )
        return JsonResponse(
            {"encontrado": True, "clave": paciente.clave, "nombre": paciente.nombres}
        )
    except Usuario.DoesNotExist:
        return JsonResponse({"encontrado": False})


@login_required
@role_required(["medico"])
def exportar_consultas_excel(request):
    # Obtener las consultas
    consultas = Consulta.objects.select_related(
        "clave_paciente", "clave_medico", "categoria_de_padecimiento"
    )

    # Convertir a una lista de diccionarios
    data = []
    for c in consultas:
        data.append(
            {
                "ID Consulta": c.id_consulta,
                "Fecha": c.fecha.strftime("%Y-%m-%d %H:%M"),
                "Paciente": f"{c.clave_paciente.nombres} {c.clave_paciente.apellido_paterno} {c.clave_paciente.apellido_materno}"
                if c.clave_paciente
                else "—",
                "Médico": f"{c.clave_medico.nombres} {c.clave_medico.apellido_paterno} {c.clave_medico.apellido_materno}"
                if c.clave_medico
                else "—",
                "Categoría de padecimiento": c.categoria_de_padecimiento.padecimiento
                if c.categoria_de_padecimiento
                else "—",
                "Padecimiento actual": c.padecimiento_actual,
                "Tratamiento no farmacológico": c.tratamiento_no_farmacologico or "",
                "Tratamiento farmacológico recetado": c.tratamiento_farmacologico_recetado
                or "",
                "Peso": c.signos_vitales.peso,
                "Talla": c.signos_vitales.talla,
                "Temperatura": c.signos_vitales.temperatura,
                "Frecuencia cardíaca": c.signos_vitales.frecuencia_cardiaca,
                "Frecuencia respiratoria": c.signos_vitales.frecuencia_respiratoria,
                "Presión arterial": c.signos_vitales.presion_arterial,
                "IMC": c.signos_vitales.imc,
            }
        )

    # Crear el DataFrame
    df = pd.DataFrame(data)
    fecha_y_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Exportar a Excel (en memoria)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f"attachment; filename=consultas_medicas_{fecha_y_hora_actual}.xlsx"
    )

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consultas Médicas")

    return response

