# dashboard_utils.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.db.models import Count
from apps.consultas.models import Consulta, CategoriaPadecimiento
from apps.usuarios.models import Usuario, HistorialMedico


def generate_habitos_figure():
    historiales = HistorialMedico.objects.filter(paciente__is_active=True)
    habitos = {
        "Fuman": historiales.filter(usa_cigarro=True).count(),
        "Ingiere alcohol": historiales.filter(ingiere_alcohol=True).count(),
        "Usa drogas": historiales.filter(usa_drogas=True).count(),
        "Embarazadas": historiales.filter(es_embarazada=True).count(),
        "Usa lentes": historiales.filter(usa_lentes=True).count(),
        "Vida sexual activa": historiales.filter(vida_sexual_activa=True).count(),
        "Usa métodos anticonceptivos": historiales.filter(
            usa_metodos_anticonceptivos=True
        ).count(),
    }
    fig = go.Figure(
        [
            go.Bar(
                x=list(habitos.keys()),
                y=list(habitos.values()),
                marker_color="indianred",
            )
        ]
    )
    fig.update_layout(
        title_text="Pacientes con hábitos", xaxis_title="Hábito", yaxis_title="Cantidad"
    )
    return fig


def generate_consultas_figure():
    consultas = Consulta.objects.values("categoria_de_padecimiento").annotate(
        total=Count("categoria_de_padecimiento")
    )
    padecimientos_dict = {
        p.id_padecimiento: p.padecimiento for p in CategoriaPadecimiento.objects.all()
    }

    if consultas:
        fig = px.bar(
            x=[
                padecimientos_dict.get(c["categoria_de_padecimiento"], "OTROS")
                for c in consultas
            ],
            y=[c["total"] for c in consultas],
            title="Distribución de tipos de consultas",
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title="Distribución de tipos de consultas",
            annotations=[
                {
                    "text": "No hay datos de consultas",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 18},
                }
            ],
        )
    return fig


def generate_area_distribution_figure():
    datos = (
        Usuario.objects.values("carrera_o_puesto_id")
        .annotate(total=Count("carrera_o_puesto_id"))
        .exclude(carrera_o_puesto_id="Médico")
    )
    fig = go.Figure(
        [
            go.Bar(
                x=[d["carrera_o_puesto_id"] for d in datos],
                y=[d["total"] for d in datos],
                marker_color="indianred",
            )
        ]
    )
    fig.update_layout(
        title_text="Distribución de áreas", xaxis_title="Área", yaxis_title="Cantidad"
    )
    return fig


def generate_area_vs_padecimientos_figure():
    datos = Consulta.objects.values(
        "clave_paciente__carrera_o_puesto_id", "categoria_de_padecimiento"
    ).annotate(total=Count("clave_paciente__carrera_o_puesto_id"))
    padecimientos_dict = {
        p.id_padecimiento: p.padecimiento for p in CategoriaPadecimiento.objects.all()
    }

    if datos:
        df = pd.DataFrame(datos)
        df["categoria_de_padecimiento"] = df["categoria_de_padecimiento"].map(
            padecimientos_dict
        )
        labels = {
            "categoria_de_padecimiento": "Categoría de padecimiento",
            "total": "Total de pacientes",
            "clave_paciente__carrera_o_puesto_id": "Área o puesto",
        }
        fig = px.bar(
            df,
            x="categoria_de_padecimiento",
            y="total",
            color="clave_paciente__carrera_o_puesto_id",
            barmode="group",
            title="Distribución de pacientes por área y tipo de consulta",
            labels=labels,
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title="Distribución de pacientes por área y tipo de consulta",
            annotations=[
                {
                    "text": "No hay datos suficientes",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 18},
                }
            ],
        )
    return fig


def generate_gender_figures():
    pacientes = Consulta.objects.values(
        "clave_paciente__clave",
        "clave_paciente__sexo",
        "clave_paciente__carrera_o_puesto_id",
    )
    df = pd.DataFrame(pacientes).drop_duplicates(subset=["clave_paciente__clave"])

    if not df.empty:
        cantidad_hombres = df[df["clave_paciente__sexo"] == "M"].count()[
            "clave_paciente__clave"
        ]
        cantidad_mujeres = df[df["clave_paciente__sexo"] == "F"].count()[
            "clave_paciente__clave"
        ]

        df_grouped = (
            df.groupby(["clave_paciente__carrera_o_puesto_id", "clave_paciente__sexo"])
            .size()
            .reset_index(name="cantidad")
        )

        bar_fig = px.bar(
            df_grouped,
            x="clave_paciente__carrera_o_puesto_id",
            y="cantidad",
            color="clave_paciente__sexo",
            barmode="group",
            title="Cantidad de pacientes por carrera/puesto y género",
            labels={
                "clave_paciente__carrera_o_puesto_id": "Carrera/puesto",
                "cantidad": "Cantidad de pacientes",
                "clave_paciente__sexo": "Género",
            },
        )

        pie_fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Hombres", "Mujeres"],
                    values=[cantidad_hombres, cantidad_mujeres],
                )
            ]
        )
        pie_fig.update_layout(
            title_text="Distribución de pacientes por género", title_x=0.5
        )
    else:
        bar_fig = go.Figure()
        bar_fig.update_layout(
            title="Cantidad de Pacientes por Carrera/puesto y género",
            annotations=[
                {
                    "text": "No hay datos de género",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 18},
                }
            ],
        )

        pie_fig = go.Figure()
        pie_fig.update_layout(
            title="Distribución de Pacientes por Género",
            annotations=[
                {
                    "text": "No hay datos disponibles",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 18},
                }
            ],
        )

    return bar_fig, pie_fig
