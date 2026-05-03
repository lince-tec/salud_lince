import pandas as pd
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.usuarios.decorators import role_required

from apps.consultas.models import Consulta
from apps.usuarios.models import HistorialMedico

#Fiunciones auxiliares
def si_no(valor):
    return "Sí" if valor else "No"
    
def clasificar_imc(imc):
    if imc is None:
        return " "
    if imc < 18.5:
        return "BP"
    elif 18.5 <= imc < 25:
        return "PI"
    elif imc < 30:
        return "SP"
    elif imc < 35:
        return "OG I"
    elif imc < 40:
        return "OG II"
    elif imc < 50:
        return "OG III"
    else: 
        return "OG IV"
    
def obtener_consultas(periodo, anio, mes=None, trimestre=None):

    if periodo == "mensual":
        consultas = Consulta.objects.filter(
            fecha__year = anio,
            fecha__month = int(mes)
        )
    elif periodo == "trimestral":
        TRIMESTRE = {
            1:(1,3),
            2:(4,6),
            3:(7,9),
            4:(10,12),
        }
        mes_inicio, mes_fin = TRIMESTRE[int(trimestre)]

        consultas = Consulta.objects.filter(
            fecha__year = anio,
            fecha__month__gte = mes_inicio,
            fecha__month__lte = mes_fin
        )
    else:
        return None
    
    return consultas.select_related("clave_paciente", "signos_vitales").order_by("fecha")

def construir_df_r09(consultas):
    #Dataframe R09
    data = []

    for c in consultas:
        paciente = c.clave_paciente
        historial = getattr(paciente, "historial", None)
        signos = getattr(c, "signos_vitales", None)

        data.append({
            # ===== DATOS PACIENTE =====
            "Fecha": f"{c.fecha.strftime('%d/%m/%Y')}",
            "Nombre y apellido": f"{paciente.nombres} {paciente.apellido_paterno}",
            "Matricula": f"{paciente.clave}",
            "Carrera": f"{paciente.carrera_o_puesto}",

            # ===== SIGNOS VITALES =====
            "Peso": signos.peso if signos else "",
            "Talla": signos.talla if signos else "",
            "IMC": signos.imc if signos else "",

            # ===== HÁBITOS ====
            "Tabaquismo": si_no(historial.usa_cigarro) if historial else "No",
            "Alcoholismo": si_no(historial.ingiere_alcohol) if historial else "No",
            "Agudeza Visual": si_no(historial.usa_lentes) if historial else "No",
            "Patologías": historial.enfermedades_cronicas if historial else " ",
            "Usaría MPF": si_no(historial.usa_metodos_anticonceptivos) if historial else "No",
            "Emabaraza": si_no(historial.es_embarazada) if historial else "No",
            "Estado nutricional" : clasificar_imc(signos.imc) if signos else " ",
            "Adicciones": si_no(historial.usa_drogas) if historial else "No",

        })
    return pd.DataFrame(data)

def construir_tabla_r10(df):
        #Tabla en la hoja R10
    tabla = df.groupby("Carrera").agg(
        Bajo_peso = ("Estado nutricional", lambda x: (x == "BP").sum()),
        Peso_ideal = ("Estado nutricional", lambda x: (x == "PI").sum()),
        Sobrepeso = ("Estado nutricional", lambda x: (x == "SP").sum()),
        Obesidad = ("Estado nutricional", lambda x: x.isin(["OG I", "OG II", "OG III", "OG IV"]).sum()),
        Alcoholismo = ("Alcoholismo", lambda x: (x == "Sí").sum()),
        Tabaquismo = ("Tabaquismo", lambda x: (x == "Sí").sum()),
        Vista_normal = ("Agudeza Visual", lambda x: (x == "No").sum()),
        Usa_lentes = ("Agudeza Visual", lambda x: (x == "Sí").sum()),
    ).reset_index()

    #colmnas manuales R10
    matricula_anio = {
        "Ing. Bioquimica": 0,
        "Ing. Electromecánica": 0,
        "Lic. Gastronomia": 0,
        "Ing. Industrial": 0,
        "Ing. Mecatrónica": 0,
        "Ing. Sistemas Computacionales":0,
        "Maestria en Ingenieria": 0,
    }

    expediente_clinico = {
        "Ing. Bioquimica": 0,
        "Ing. Electromecánica": 0,
        "Lic. Gastronomia": 0,
        "Ing. Industrial": 0,
        "Ing. Mecatrónica": 0,
        "Ing. Sistemas Computacionales": 0,
        "Maestria en Ingenieria": 0,
    }

    tabla["Matricula_año"] = tabla["Carrera"].map(matricula_anio)
    tabla["Expediente_clinico"] = tabla["Carrera"].map(expediente_clinico)

    #reordenar columnas R10
    return tabla[[
        "Carrera",
        "Matricula_año",
        "Expediente_clinico",
        "Bajo_peso",
        "Peso_ideal",
        "Sobrepeso",    
        "Obesidad",
        "Alcoholismo",
        "Tabaquismo",
        "Vista_normal",
        "Usa_lentes",
    ]]
 
 #Función para crerar gráficas
def crear_grafica(workbook, worksheet, tabla, columnas,nombre_columnas, titulo, posicion):
    
    chart = workbook.add_chart({"type": "column"})
        
    for col_nombre in nombre_columnas:
        col = columnas[col_nombre]

        chart.add_series({
            "name": ["R10", 0, col],
            "categories": ["R10", 1, columnas["Carrera"], len(tabla), columnas["Carrera"]],
            "values": ["R10", 1, col, len(tabla), col],
            "data_labels": {"value": True},
        })

    chart.set_title({"name": titulo})
    chart.set_x_axis({"name": "Carrera"})

    worksheet.insert_chart(posicion, chart)

#Funció principal para exportar el reporte
@login_required
@role_required(["medico"])
def exportar_reporte_r09(request):
    
    periodo = request.GET.get("periodo")
    anio = int(request.GET.get("anio"))
    mes = request.GET.get("mes")
    trimestre = request.GET.get("trimestre")

    consultas = obtener_consultas(periodo, anio, mes, trimestre)

    if consultas is None:
        return HttpResponse("Periodo no válido")
    
    df = construir_df_r09(consultas)

    if df.empty:
        return HttpResponse("No hay datos para el periodo seleccionado")
    
    tabla = construir_tabla_r10(df)

    #Crear archivo Excel
    output = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    output["Content-Disposition"] = f'attachment; filename="R09_{anio}_{periodo}.xlsx"'

    writer = pd.ExcelWriter(output, engine="xlsxwriter")

    df.to_excel(writer, sheet_name=f"R09_Semestre {periodo}", index=False)
    tabla.to_excel(writer, sheet_name="R10", index=False)

    workbook = writer.book
    worksheet = writer.sheets["R10"]

    columnas = {col: i for i, col in enumerate(tabla.columns)}

    crear_grafica(workbook, worksheet, tabla, columnas,
                  ["Bajo_peso", "Peso_ideal", "Sobrepeso", "Obesidad"],
                  "ÍNDICE DE MASA CORPORAL", "B18")

    crear_grafica(workbook, worksheet, tabla, columnas,
                  ["Alcoholismo", "Tabaquismo"],
                  "ADICCIONES", "P25")

    crear_grafica(workbook, worksheet, tabla, columnas,
                  ["Vista_normal", "Usa_lentes"],
                  "AGUDEZA VISUAL", "B38")

    crear_grafica(workbook, worksheet, tabla, columnas,
                  ["Matricula_año", "Expediente_clinico"],
                  "GRÁFICA COMPARATIVA MEDICINA PREVENTIVA", "P8")

    writer.close()

    return output