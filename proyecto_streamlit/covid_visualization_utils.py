"""
Funciones de visualizacion para el dashboard COVID.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from covid_dataframe_utils import (
    DatasetValidationError,
    prepare_clean_dataframe,
    require_columns,
)


DEFAULT_PALETTE = [
    "#0f766e",
    "#2563eb",
    "#f97316",
    "#dc2626",
    "#7c3aed",
    "#ca8a04",
    "#0891b2",
]


def plot_general_cases_forecast(
    monthly_cases: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_method: str,
) -> go.Figure:
    """Grafica la serie temporal general de casos con pronostico."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_cases["ds"],
            y=monthly_cases["y"],
            mode="lines+markers",
            name="Historico",
            line={"color": DEFAULT_PALETTE[0], "width": 3},
        )
    )

    forecast_only = forecast_df[forecast_df["tipo"] == "pronostico"].copy()
    if not forecast_only.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_only["ds"],
                y=forecast_only["yhat"],
                mode="lines+markers",
                name=f"Pronostico ({forecast_method})",
                line={"color": DEFAULT_PALETTE[2], "width": 3, "dash": "dash"},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.concat([forecast_only["ds"], forecast_only["ds"][::-1]]),
                y=pd.concat([forecast_only["yhat_upper"], forecast_only["yhat_lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(249,115,22,0.18)",
                line={"color": "rgba(0,0,0,0)"},
                hoverinfo="skip",
                name="Banda de confianza",
            )
        )

    fig.update_layout(
        title="Serie temporal general de casos con pronostico",
        xaxis_title="Mes",
        yaxis_title="Numero de casos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_top_departments_time_series(df: pd.DataFrame, top_n: int = 5) -> go.Figure:
    """Grafica la evolucion temporal de los departamentos con mas casos."""
    top_departments = (
        df["departamento_nom"]
        .fillna("Sin dato")
        .value_counts()
        .head(top_n)
        .index.tolist()
    )

    dept_df = df[df["departamento_nom"].isin(top_departments)].copy()
    grouped = (
        dept_df.groupby(["mes_reporte", "departamento_nom"], dropna=False)
        .size()
        .reset_index(name="casos")
    )
    grouped["mes_reporte"] = pd.to_datetime(grouped["mes_reporte"], errors="coerce")
    grouped = grouped.dropna(subset=["mes_reporte"]).sort_values("mes_reporte")

    fig = go.Figure()
    for idx, department in enumerate(top_departments):
        subset = grouped[grouped["departamento_nom"] == department]
        fig.add_trace(
            go.Scatter(
                x=subset["mes_reporte"],
                y=subset["casos"],
                mode="lines+markers",
                name=department,
                line={"width": 3, "color": DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]},
            )
        )

    fig.update_layout(
        title=f"Top {top_n} departamentos con mas casos",
        xaxis_title="Mes de reporte",
        yaxis_title="Numero de casos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_mortality_forecast(
    monthly_deaths: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_method: str,
) -> go.Figure:
    """Grafica mortalidad historica y proyectada."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_deaths["ds"],
            y=monthly_deaths["y"],
            mode="lines+markers",
            name="Historico",
            line={"color": DEFAULT_PALETTE[3], "width": 3},
        )
    )

    forecast_only = forecast_df[forecast_df["tipo"] == "pronostico"].copy()
    if not forecast_only.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_only["ds"],
                y=forecast_only["yhat"],
                mode="lines+markers",
                name=f"Pronostico ({forecast_method})",
                line={"color": DEFAULT_PALETTE[4], "width": 3, "dash": "dash"},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.concat([forecast_only["ds"], forecast_only["ds"][::-1]]),
                y=pd.concat([forecast_only["yhat_upper"], forecast_only["yhat_lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(124,58,237,0.18)",
                line={"color": "rgba(0,0,0,0)"},
                hoverinfo="skip",
                name="Banda de confianza",
            )
        )

    fig.update_layout(
        title="Mortalidad mensual con pronostico",
        xaxis_title="Mes",
        yaxis_title="Numero de fallecimientos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_age_group_stacked_area(df: pd.DataFrame) -> go.Figure:
    """Grafica la evolucion temporal de casos por grupo etario."""
    grouped = (
        df.groupby(["mes_reporte", "grupo_edad"], dropna=False)
        .size()
        .reset_index(name="casos")
    )
    grouped["mes_reporte"] = pd.to_datetime(grouped["mes_reporte"], errors="coerce")
    grouped = grouped.dropna(subset=["mes_reporte"])

    pivot_df = (
        grouped.pivot_table(
            index="mes_reporte",
            columns="grupo_edad",
            values="casos",
            fill_value=0,
        )
        .sort_index()
    )

    age_order = ["0-17", "18-29", "30-44", "45-59", "60+"]
    ordered_columns = [col for col in age_order if col in pivot_df.columns] + [
        col for col in pivot_df.columns if col not in age_order
    ]
    pivot_df = pivot_df[ordered_columns]

    fig = go.Figure()
    for idx, age_group in enumerate(pivot_df.columns):
        fig.add_trace(
            go.Scatter(
                x=pivot_df.index,
                y=pivot_df[age_group],
                mode="lines",
                stackgroup="one",
                name=str(age_group),
                line={"width": 1.5, "color": DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]},
            )
        )

    fig.update_layout(
        title="Evolucion de casos por grupo de edad",
        xaxis_title="Mes de reporte",
        yaxis_title="Numero de casos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_cases_by_department(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Grafico de barras con cantidad de casos por departamento."""
    require_columns(df, {"departamento_nom"}, "grafico de casos por departamento")

    grouped = (
        df["departamento_nom"]
        .fillna("Sin dato")
        .value_counts()
        .head(top_n)
        .rename_axis("departamento_nom")
        .reset_index(name="casos")
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=grouped["departamento_nom"],
                y=grouped["casos"],
                marker_color=DEFAULT_PALETTE[0],
                text=grouped["casos"],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=f"Top {top_n} departamentos por cantidad de casos",
        xaxis_title="Departamento",
        yaxis_title="Numero de casos",
        template="plotly_white",
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def plot_cases_by_city(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Grafico de barras con cantidad de casos por ciudad."""
    require_columns(df, {"ciudad_municipio_nom"}, "grafico de casos por ciudad")

    grouped = (
        df["ciudad_municipio_nom"]
        .fillna("Sin dato")
        .value_counts()
        .head(top_n)
        .rename_axis("ciudad_municipio_nom")
        .reset_index(name="casos")
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=grouped["ciudad_municipio_nom"],
                y=grouped["casos"],
                marker_color=DEFAULT_PALETTE[1],
                text=grouped["casos"],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=f"Top {top_n} ciudades por cantidad de casos",
        xaxis_title="Ciudad",
        yaxis_title="Numero de casos",
        template="plotly_white",
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def plot_health_state_trends(
    df: pd.DataFrame,
    states: list[str],
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> go.Figure:
    """Grafica la tendencia temporal de 1 a 3 estados de salud."""
    require_columns(df, {"estado"}, "grafico de tendencia de estados de salud")

    if not states:
        raise DatasetValidationError(
            "La funcion `plot_health_state_trends` requiere al menos 1 estado."
        )

    if len(states) > 3:
        raise DatasetValidationError(
            "La funcion `plot_health_state_trends` permite maximo 3 estados."
        )

    working = prepare_clean_dataframe(df)
    if "mes_reporte" not in working.columns and "fecha_reporte_web" not in working.columns:
        raise DatasetValidationError(
            "Se requiere `mes_reporte` o `fecha_reporte_web` para graficar tendencias."
        )

    existing_states = set(working["estado"].dropna().astype(str).unique())
    missing_states = [state for state in states if state not in existing_states]
    if missing_states:
        raise DatasetValidationError(
            "Los siguientes estados no existen en los datos: " + ", ".join(missing_states)
        )

    filtered = working[working["estado"].isin(states)].copy()

    if start_date is not None:
        start_date = pd.to_datetime(start_date, errors="coerce")
        if pd.isna(start_date):
            raise DatasetValidationError("`start_date` no es una fecha valida.")
        filtered = filtered[filtered["mes_reporte_fecha"] >= start_date]

    if end_date is not None:
        end_date = pd.to_datetime(end_date, errors="coerce")
        if pd.isna(end_date):
            raise DatasetValidationError("`end_date` no es una fecha valida.")
        filtered = filtered[filtered["mes_reporte_fecha"] <= end_date]

    grouped = (
        filtered.groupby(["mes_reporte", "estado"], dropna=False)
        .size()
        .reset_index(name="casos")
    )
    grouped["mes_reporte"] = pd.to_datetime(grouped["mes_reporte"], errors="coerce")
    grouped = grouped.dropna(subset=["mes_reporte"]).sort_values("mes_reporte")

    fig = go.Figure()
    for idx, state in enumerate(states):
        subset = grouped[grouped["estado"] == state]
        fig.add_trace(
            go.Scatter(
                x=subset["mes_reporte"],
                y=subset["casos"],
                mode="lines+markers",
                name=state,
                line={"width": 3, "color": DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]},
            )
        )

    subtitle_parts = []
    if start_date is not None:
        subtitle_parts.append(f"desde {pd.to_datetime(start_date).strftime('%Y-%m-%d')}")
    if end_date is not None:
        subtitle_parts.append(f"hasta {pd.to_datetime(end_date).strftime('%Y-%m-%d')}")
    subtitle = f" ({', '.join(subtitle_parts)})" if subtitle_parts else ""

    fig.update_layout(
        title=f"Tendencia temporal de estados de salud{subtitle}",
        xaxis_title="Mes de reporte",
        yaxis_title="Numero de casos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_gender_distribution_deceased(df: pd.DataFrame) -> go.Figure:
    """Diagrama de torta con distribucion por sexo de casos fallecidos."""
    require_columns(
        df,
        {"estado", "sexo"},
        "diagrama de torta de distribucion por sexo en fallecidos",
    )

    deceased_df = df[df["estado"].astype("string").str.strip().eq("Fallecido")].copy()
    if deceased_df.empty:
        raise DatasetValidationError("No hay registros con estado 'Fallecido' para graficar.")

    deceased_df["sexo"] = deceased_df["sexo"].fillna("Sin dato").astype(str).replace(
        {
            "M": "Masculino",
            "F": "Femenino",
        }
    )

    grouped = deceased_df["sexo"].value_counts().rename_axis("sexo").reset_index(name="casos")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=grouped["sexo"],
                values=grouped["casos"],
                hole=0.25,
                textinfo="label+percent",
                marker={"colors": DEFAULT_PALETTE[: len(grouped)]},
            )
        ]
    )
    fig.update_layout(
        title="Distribucion por sexo en casos fallecidos",
        template="plotly_white",
    )
    return fig


def generate_additional_plots(df: pd.DataFrame) -> dict[str, go.Figure]:
    """Genera el conjunto de graficas adicionales solicitadas."""
    return generate_additional_plots_with_options(df)


def generate_additional_plots_with_options(
    df: pd.DataFrame,
    selected_states: list[str] | None = None,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> dict[str, go.Figure]:
    """Genera el conjunto de graficas adicionales con opciones de filtrado."""
    working = prepare_clean_dataframe(df)
    try:
        states_for_trend = selected_states or select_default_health_states(working)
        health_state_fig = plot_health_state_trends(
            working,
            states_for_trend,
            start_date=start_date,
            end_date=end_date,
        )
    except DatasetValidationError:
        health_state_fig = build_info_figure(
            "Tendencia de estados de salud",
            "No hay al menos 3 estados distintos en el dataset actual para construir esta grafica.",
        )

    try:
        gender_deceased_fig = plot_gender_distribution_deceased(working)
    except DatasetValidationError:
        gender_deceased_fig = build_info_figure(
            "Distribucion por sexo en casos fallecidos",
            "No hay registros fallecidos para el filtro actual.",
        )

    return {
        "fig_cases_by_department": plot_cases_by_department(working),
        "fig_cases_by_city": plot_cases_by_city(working),
        "fig_health_state_trends": health_state_fig,
        "fig_gender_distribution_deceased": gender_deceased_fig,
    }


def select_default_health_states(df: pd.DataFrame) -> list[str]:
    """Selecciona hasta 3 estados existentes priorizando los mas utiles para lectura."""
    require_columns(df, {"estado"}, "seleccion de estados por defecto")

    available_states = df["estado"].dropna().astype(str)
    available_set = set(available_states.unique())
    preferred_order = ["Leve", "Grave", "Fallecido", "Moderado", "Asintomatico"]

    selected = [state for state in preferred_order if state in available_set]
    if len(selected) < 3:
        top_states = available_states.value_counts().index.tolist()
        for state in top_states:
            if state not in selected:
                selected.append(state)
            if len(selected) == 3:
                break

    if len(selected) < 3:
        raise DatasetValidationError(
            "No hay suficientes estados distintos en el dataset para construir la tendencia de estados."
        )

    return selected[:3]


def build_info_figure(title: str, message: str) -> go.Figure:
    """Construye una figura simple para informar que una grafica no aplica."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 14},
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig


def build_combined_dashboard(
    cases_fig: go.Figure,
    top_departments_fig: go.Figure,
    mortality_fig: go.Figure,
    age_fig: go.Figure,
) -> go.Figure:
    """Combina las 4 visualizaciones en un solo dashboard."""
    dashboard = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "Casos con pronostico",
            "Top 5 departamentos",
            "Mortalidad con pronostico",
            "Grupos de edad",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    for trace in cases_fig.data:
        dashboard.add_trace(trace, row=1, col=1)
    for trace in top_departments_fig.data:
        dashboard.add_trace(trace, row=1, col=2)
    for trace in mortality_fig.data:
        dashboard.add_trace(trace, row=2, col=1)
    for trace in age_fig.data:
        dashboard.add_trace(trace, row=2, col=2)

    dashboard.update_layout(
        title="Dashboard COVID Colombia: analisis descriptivo y predictivo",
        template="plotly_white",
        height=900,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    dashboard.update_xaxes(title_text="Mes", row=1, col=1)
    dashboard.update_xaxes(title_text="Mes", row=1, col=2)
    dashboard.update_xaxes(title_text="Mes", row=2, col=1)
    dashboard.update_xaxes(title_text="Mes", row=2, col=2)
    dashboard.update_yaxes(title_text="Casos", row=1, col=1)
    dashboard.update_yaxes(title_text="Casos", row=1, col=2)
    dashboard.update_yaxes(title_text="Fallecimientos", row=2, col=1)
    dashboard.update_yaxes(title_text="Casos", row=2, col=2)

    return dashboard
