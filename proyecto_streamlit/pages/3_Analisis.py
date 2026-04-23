"""
Pagina de analisis descriptivo y predictivo del dataset COVID.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from covid_dashboard_module import DatasetValidationError, generate_dashboard_from_dataframe
from dashboard_page_utils import (
    apply_common_filters,
    dataframe_to_csv_bytes,
    get_dataset_overview,
    get_default_trend_states,
    get_filter_options,
    load_collection_dataframe,
    prepare_dashboard_dataframe,
)
from ui_styles import apply_shared_styles, render_hero

load_dotenv()

st.set_page_config(page_title="Analisis", page_icon="📈", layout="wide")
apply_shared_styles()


def apply_analysis_page_styles() -> None:
    """Sin estilos extra: se conserva el diseno simple."""
    return None


def render_analysis_metric_grid(metrics: list[dict[str, str]]) -> None:
    columns = st.columns(4)
    for idx, metric in enumerate(metrics):
        col = columns[idx % 4]
        with col:
            col.metric(metric["label"], metric["value"], help=metric["sub"])


def render_analysis_section_header(title: str, icon: str) -> None:
    st.subheader(title)


def render_analysis_question_list(questions: list[str]) -> None:
    left, right = st.columns(2)
    midpoint = (len(questions) + 1) // 2
    with left:
        for idx, question in enumerate(questions[:midpoint], start=1):
            st.markdown(f"{idx}. {question}")
    with right:
        for idx, question in enumerate(questions[midpoint:], start=midpoint + 1):
            st.markdown(f"{idx}. {question}")


def render_analysis_notes(notes: list[str]) -> None:
    left, right = st.columns(2)
    pairs = [notes[:2], notes[2:]]
    for col, group in zip((left, right), pairs):
        with col:
            for note in group:
                st.info(to_display_markdown(note))


apply_analysis_page_styles()


def build_simple_bar(
    summary_df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_title: str,
    y_title: str,
    color: str,
) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=summary_df[x_col],
                y=summary_df[y_col],
                marker_color=color,
                text=summary_df[y_col],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
    )
    fig.update_xaxes(tickangle=-25)
    return fig


def build_info_figure(title: str, message: str) -> go.Figure:
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


def build_top_months_bar(monthly_df: pd.DataFrame, top_n: int = 6) -> go.Figure:
    working = monthly_df.copy().sort_values("y", ascending=False).head(top_n)
    working["Mes"] = pd.to_datetime(working["ds"]).dt.strftime("%Y-%m")
    return build_simple_bar(
        working,
        x_col="Mes",
        y_col="y",
        title=f"Top {top_n} meses con mayor volumen de casos",
        x_title="Mes",
        y_title="Numero de casos",
        color="#0f766e",
    )


def build_monthly_change_chart(monthly_df: pd.DataFrame) -> go.Figure:
    working = monthly_df.copy().sort_values("ds")
    working["variacion"] = working["y"].diff().fillna(0)
    colors = ["#0f766e" if value >= 0 else "#dc2626" for value in working["variacion"]]
    fig = go.Figure(
        data=[
            go.Bar(
                x=working["ds"],
                y=working["variacion"],
                marker_color=colors,
                name="Variacion mensual",
            )
        ]
    )
    fig.update_layout(
        title="Cambio mes a mes en el volumen de casos",
        xaxis_title="Mes",
        yaxis_title="Diferencia frente al mes anterior",
        template="plotly_white",
    )
    return fig


def build_share_donut(
    summary_df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
) -> go.Figure:
    if summary_df.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")
    fig = go.Figure(
        data=[
            go.Pie(
                labels=summary_df[label_col],
                values=summary_df[value_col],
                hole=0.45,
                textinfo="label+percent",
            )
        ]
    )
    fig.update_layout(title=title, template="plotly_white")
    return fig


def build_multi_line_trend(df: pd.DataFrame, category_col: str, title: str) -> go.Figure:
    if category_col not in df.columns:
        return build_info_figure(title, "La columna requerida no existe en el dataset filtrado.")

    grouped = (
        df.groupby(["mes_reporte", category_col], dropna=False)
        .size()
        .reset_index(name="casos")
    )
    grouped["mes_reporte"] = pd.to_datetime(grouped["mes_reporte"], errors="coerce")
    grouped = grouped.dropna(subset=["mes_reporte"]).sort_values("mes_reporte")
    if grouped.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")

    fig = go.Figure()
    categories = grouped[category_col].fillna("Sin dato").astype(str).value_counts().index.tolist()
    for category in categories[:6]:
        subset = grouped[grouped[category_col].fillna("Sin dato").astype(str) == category]
        fig.add_trace(
            go.Scatter(
                x=subset["mes_reporte"],
                y=subset["casos"],
                mode="lines+markers",
                name=str(category),
                line={"width": 3},
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Mes",
        yaxis_title="Numero de casos",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def build_cases_vs_deaths_combo(cases_df: pd.DataFrame, deaths_df: pd.DataFrame) -> go.Figure:
    merged = cases_df.merge(deaths_df, on="ds", how="left", suffixes=("_casos", "_muertes")).fillna(0)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=merged["ds"],
            y=merged["y_casos"],
            name="Casos",
            marker_color="#0f766e",
            opacity=0.68,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=merged["ds"],
            y=merged["y_muertes"],
            name="Fallecimientos",
            mode="lines+markers",
            line={"color": "#dc2626", "width": 3},
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Casos y fallecimientos en una misma linea temporal",
        xaxis_title="Mes",
        yaxis={"title": "Casos"},
        yaxis2={"title": "Fallecimientos", "overlaying": "y", "side": "right"},
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def build_cases_vs_deaths_scatter(cases_df: pd.DataFrame, deaths_df: pd.DataFrame) -> go.Figure:
    merged = cases_df.merge(deaths_df, on="ds", how="left", suffixes=("_casos", "_muertes")).fillna(0)
    merged["etiqueta_mes"] = pd.to_datetime(merged["ds"]).dt.strftime("%Y-%m")
    fig = go.Figure(
        data=[
            go.Scatter(
                x=merged["y_casos"],
                y=merged["y_muertes"],
                mode="markers+text",
                text=merged["etiqueta_mes"],
                textposition="top center",
                marker={"size": 11, "color": "#2563eb", "opacity": 0.8},
                name="Meses",
            )
        ]
    )
    fig.update_layout(
        title="Relacion entre volumen de casos y fallecimientos",
        xaxis_title="Casos mensuales",
        yaxis_title="Fallecimientos mensuales",
        template="plotly_white",
    )
    return fig


def build_group_metric_bar(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    title: str,
    y_title: str,
    top_n: int | None = None,
    color: str = "#2563eb",
) -> go.Figure:
    if group_col not in df.columns or value_col not in df.columns:
        return build_info_figure(title, "No estan disponibles las columnas requeridas.")

    working = df[[group_col, value_col]].copy().dropna()
    if working.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")

    summary = (
        working.groupby(group_col, dropna=False)[value_col]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    if top_n is not None:
        summary = summary.head(top_n)
    summary[value_col] = summary[value_col].round(2)
    return build_simple_bar(
        summary,
        x_col=group_col,
        y_col=value_col,
        title=title,
        x_title=group_col.replace("_", " ").title(),
        y_title=y_title,
        color=color,
    )


def build_delay_distribution(df: pd.DataFrame, value_col: str, title: str) -> go.Figure:
    if value_col not in df.columns:
        return build_info_figure(title, "No esta disponible la variable requerida.")
    working = df[value_col].dropna()
    if working.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")
    fig = go.Figure(
        data=[
            go.Histogram(
                x=working,
                nbinsx=20,
                marker_color="#0891b2",
                name="Distribucion",
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis_title="Dias",
        yaxis_title="Numero de casos",
        template="plotly_white",
    )
    return fig


def build_delay_boxplot(df: pd.DataFrame, group_col: str, value_col: str, title: str) -> go.Figure:
    if group_col not in df.columns or value_col not in df.columns:
        return build_info_figure(title, "No estan disponibles las columnas requeridas.")
    working = df[[group_col, value_col]].copy().dropna()
    if working.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")
    fig = go.Figure()
    categories = working[group_col].fillna("Sin dato").astype(str).value_counts().index.tolist()
    for category in categories[:8]:
        subset = working[working[group_col].fillna("Sin dato").astype(str) == category]
        fig.add_trace(
            go.Box(
                y=subset[value_col],
                name=str(category),
                boxmean=True,
            )
        )
    fig.update_layout(
        title=title,
        yaxis_title="Dias",
        template="plotly_white",
    )
    return fig


def build_mortality_rate_bar(
    df: pd.DataFrame,
    group_col: str,
    title: str,
    top_n: int | None = None,
    min_cases: int = 5,
) -> go.Figure:
    if group_col not in df.columns:
        return build_info_figure(title, "No esta disponible la columna requerida.")
    working = df[[group_col, "estado"]].copy().dropna(subset=[group_col])
    if working.empty:
        return build_info_figure(title, "No hay datos suficientes para construir esta visualizacion.")

    summary = (
        working.groupby(group_col, dropna=False)
        .agg(
            casos=("estado", "size"),
            fallecidos=("estado", lambda s: int(s.astype("string").str.lower().eq("fallecido").sum())),
        )
        .reset_index()
    )
    summary = summary[summary["casos"] >= min_cases].copy()
    if summary.empty:
        return build_info_figure(title, "No hay grupos con suficientes casos para estimar mortalidad relativa.")
    summary["tasa_mortalidad"] = (summary["fallecidos"] / summary["casos"] * 100).round(2)
    summary = summary.sort_values("tasa_mortalidad", ascending=False)
    if top_n is not None:
        summary = summary.head(top_n)
    return build_simple_bar(
        summary,
        x_col=group_col,
        y_col="tasa_mortalidad",
        title=title,
        x_title=group_col.replace("_", " ").title(),
        y_title="Tasa de mortalidad (%)",
        color="#dc2626",
    )


def build_top_city_within_department(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return build_info_figure("Ciudades del departamento lider", "No hay datos para construir esta vista.")
    top_department_name = df["departamento_nom"].fillna("Sin dato").value_counts().idxmax()
    dept_df = df[df["departamento_nom"].fillna("Sin dato") == top_department_name].copy()
    summary = (
        dept_df["ciudad_municipio_nom"]
        .fillna("Sin dato")
        .value_counts()
        .head(8)
        .rename_axis("Ciudad")
        .reset_index(name="Casos")
    )
    return build_simple_bar(
        summary,
        x_col="Ciudad",
        y_col="Casos",
        title=f"Ciudades con mas casos dentro de {top_department_name}",
        x_title="Ciudad",
        y_title="Numero de casos",
        color="#0891b2",
    )


def build_active_filter_cards(filters: dict[str, list[str] | str]) -> str:
    cards = []
    for label, values in filters.items():
        if not values:
            continue
        if isinstance(values, list):
            preview = ", ".join(values[:3])
            if len(values) > 3:
                preview += f" +{len(values) - 3}"
        else:
            preview = str(values)
        cards.append(f'<div class="question-card"><strong>{label}</strong><br>{preview}</div>')
    if not cards:
        cards.append('<div class="question-card"><strong>Sin filtros especificos</strong><br>Se esta analizando el periodo completo con todas las categorias disponibles.</div>')
    return f'<div class="question-grid">{"".join(cards)}</div>'


def render_answer_box(title: str, body: str) -> None:
    """Renderiza una respuesta escrita basada en el analisis actual."""
    st.markdown(f"**{title}**")
    st.info(to_display_markdown(body))


def to_display_markdown(text: str) -> str:
    """Convierte HTML simple a Markdown legible para mensajes de Streamlit."""
    return (
        text.replace("<strong>", "**")
        .replace("</strong>", "**")
        .replace("<br>", "  \n")
        .replace("<br/>", "  \n")
    )


render_hero(
    "Analisis COVID",
    "Responde preguntas de negocio sobre el comportamiento temporal, territorial y demografico del dataset COVID en una sola pagina.",
    badge="Inteligencia del periodo",
)

collection_name = os.getenv("COLLECTION_NAME", "datos_api")
BUSINESS_QUESTIONS = [
    "En que meses se concentro el mayor numero de casos reportados?",
    "Que departamentos y ciudades concentran mas casos en el periodo filtrado?",
    "Que grupos de edad tienen mayor participacion y como cambia su peso en el tiempo?",
    "Existen diferencias por sexo en el total de casos y en los fallecimientos?",
    "Como se relacionan el volumen de casos y la mortalidad en el tiempo?",
    "Que territorios y poblaciones conviene priorizar cuando se analiza la severidad?",
    "Que tan rapido se diagnostican los casos y donde hay mayor demora?",
    "Como cambia el origen del contagio y la ubicacion del caso en el filtro actual?",
]
QUESTION_OPTIONS = {
    "Meses pico": BUSINESS_QUESTIONS[0],
    "Territorio": BUSINESS_QUESTIONS[1],
    "Edad": BUSINESS_QUESTIONS[2],
    "Sexo": BUSINESS_QUESTIONS[3],
    "Casos vs mortalidad": BUSINESS_QUESTIONS[4],
    "Severidad": BUSINESS_QUESTIONS[5],
    "Oportunidad diagnostica": BUSINESS_QUESTIONS[6],
    "Contagio y atencion": BUSINESS_QUESTIONS[7],
}


@st.cache_data(ttl=120, show_spinner="Construyendo analisis y graficas...")
def construir_dashboard(
    df: pd.DataFrame,
    forecast_periods: int,
    selected_states: tuple[str, ...],
    start_date: object | None,
    end_date: object | None,
):
    return generate_dashboard_from_dataframe(
        df,
        forecast_periods=forecast_periods,
        selected_states=list(selected_states),
        start_date=start_date,
        end_date=end_date,
    )


raw_df = load_collection_dataframe(collection_name)
if raw_df.empty:
    st.warning("No hay datos disponibles en MongoDB. Carga datos primero desde la pagina 1.")
    st.stop()

try:
    prepared_source_df = prepare_dashboard_dataframe(raw_df)
except DatasetValidationError as e:
    st.error(f"El dataset no se pudo preparar para analisis: {e}")
    st.stop()

overview = get_dataset_overview(prepared_source_df)
options = get_filter_options(prepared_source_df)
default_states = get_default_trend_states(prepared_source_df)

st.sidebar.header("Filtros del analisis")
forecast_periods = st.sidebar.slider(
    "Meses a pronosticar",
    min_value=3,
    max_value=12,
    value=6,
    step=1,
    help="Afecta las visualizaciones con pronostico: 'Meses pico' y 'Casos vs mortalidad'.",
)

date_range = st.sidebar.date_input(
    "Rango de meses",
    value=(options["min_date"], options["max_date"]),
    min_value=options["min_date"],
    max_value=options["max_date"],
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = options["min_date"], options["max_date"]

selected_departments = st.sidebar.multiselect("Departamentos", options=options["departments"])
selected_cities = st.sidebar.multiselect("Ciudades", options=options["cities"])
selected_sexes = st.sidebar.multiselect("Sexo", options=options["sexes"])
selected_age_groups = st.sidebar.multiselect("Grupo de edad", options=options["age_groups"])
selected_states_filter = st.sidebar.multiselect("Estado de salud", options=options["states"])
selected_contagion_sources = st.sidebar.multiselect(
    "Fuente de contagio",
    options=options["contagion_sources"],
)
selected_locations = st.sidebar.multiselect(
    "Ubicacion del caso",
    options=options["locations"],
)
selected_recovery_types = st.sidebar.multiselect(
    "Tipo de recuperacion",
    options=options["recovery_types"],
)

filtered_df = apply_common_filters(
    prepared_source_df,
    start_date=start_date,
    end_date=end_date,
    departments=selected_departments,
    cities=selected_cities,
    sexes=selected_sexes,
    age_groups=selected_age_groups,
    states=selected_states_filter,
    contagion_sources=selected_contagion_sources,
    locations=selected_locations,
    recovery_types=selected_recovery_types,
)

if filtered_df.empty:
    st.warning("No hay registros para el filtro actual. Ajusta el rango o las categorias seleccionadas.")
    st.stop()

filtered_states = sorted(filtered_df["estado"].dropna().astype(str).unique().tolist())
default_selected_states = [state for state in default_states if state in filtered_states][:3]
if len(default_selected_states) < 3:
    default_selected_states = filtered_states[:3]

trend_states = st.sidebar.multiselect(
    "Estados para comparar",
    options=filtered_states,
    default=default_selected_states,
    max_selections=3,
)
selected_trend_states = trend_states if trend_states else default_selected_states

try:
    result = construir_dashboard(
        filtered_df,
        forecast_periods,
        tuple(selected_trend_states),
        start_date,
        end_date,
    )
except DatasetValidationError as e:
    st.error(f"Error en el dataset filtrado: {e}")
    st.stop()
except Exception as e:
    st.error(f"No fue posible construir el analisis: {e}")
    st.stop()

prepared_df = result["dataframe"]
monthly_cases = result["monthly_cases"]
monthly_deaths = result["monthly_deaths"]

total_cases = len(prepared_df)
total_deaths = int(prepared_df["estado"].astype("string").str.lower().eq("fallecido").sum())
mortality_rate = (total_deaths / total_cases * 100) if total_cases else 0
top_department = prepared_df["departamento_nom"].fillna("Sin dato").value_counts().idxmax()
top_city = prepared_df["ciudad_municipio_nom"].fillna("Sin dato").value_counts().idxmax()
peak_month = monthly_cases.sort_values("y", ascending=False).iloc[0]
peak_month_label = pd.to_datetime(peak_month["ds"]).strftime("%Y-%m")
peak_month_cases = int(peak_month["y"])
monthly_change_peak = (
    monthly_cases.assign(variacion=monthly_cases["y"].diff())
    .dropna(subset=["variacion"])
    .sort_values("variacion", ascending=False)
)
largest_growth_month_label = (
    pd.to_datetime(monthly_change_peak.iloc[0]["ds"]).strftime("%Y-%m")
    if not monthly_change_peak.empty
    else "Sin dato"
)
largest_growth_value = int(monthly_change_peak.iloc[0]["variacion"]) if not monthly_change_peak.empty else 0

sex_summary = (
    prepared_df["sexo"]
    .fillna("Sin dato")
    .value_counts()
    .rename_axis("Sexo")
    .reset_index(name="Casos")
)
age_summary = (
    prepared_df["grupo_edad"]
    .fillna("Sin dato")
    .value_counts()
    .rename_axis("Grupo de edad")
    .reset_index(name="Casos")
)
contagion_summary = (
    prepared_df["fuente_tipo_contagio"]
    .fillna("Sin dato")
    .value_counts()
    .rename_axis("Fuente de contagio")
    .reset_index(name="Casos")
) if "fuente_tipo_contagio" in prepared_df.columns else pd.DataFrame()
location_summary = (
    prepared_df["ubicacion"]
    .fillna("Sin dato")
    .value_counts()
    .rename_axis("Ubicacion")
    .reset_index(name="Casos")
) if "ubicacion" in prepared_df.columns else pd.DataFrame()

leading_age_group = age_summary.iloc[0]["Grupo de edad"] if not age_summary.empty else "Sin dato"
leading_age_group_cases = int(age_summary.iloc[0]["Casos"]) if not age_summary.empty else 0
second_age_group = age_summary.iloc[1]["Grupo de edad"] if len(age_summary) > 1 else "Sin dato"
second_age_group_cases = int(age_summary.iloc[1]["Casos"]) if len(age_summary) > 1 else 0
delay_series = (
    prepared_df["dias_sintomas_a_diagnostico"].dropna()
    if "dias_sintomas_a_diagnostico" in prepared_df.columns
    else pd.Series(dtype=float)
)
mean_delay = float(delay_series.mean()) if not delay_series.empty else None
median_delay = float(delay_series.median()) if not delay_series.empty else None
top_sex = sex_summary.iloc[0]["Sexo"] if not sex_summary.empty else "Sin dato"
top_sex_cases = int(sex_summary.iloc[0]["Casos"]) if not sex_summary.empty else 0
top_contagion = (
    contagion_summary.iloc[0]["Fuente de contagio"] if not contagion_summary.empty else "Sin dato"
)
top_contagion_cases = int(contagion_summary.iloc[0]["Casos"]) if not contagion_summary.empty else 0
top_location = location_summary.iloc[0]["Ubicacion"] if not location_summary.empty else "Sin dato"
top_location_cases = int(location_summary.iloc[0]["Casos"]) if not location_summary.empty else 0

age_mortality_summary = (
    prepared_df.groupby("grupo_edad", dropna=False)
    .agg(
        casos=("estado", "size"),
        fallecidos=("estado", lambda s: int(s.astype("string").str.lower().eq("fallecido").sum())),
    )
    .reset_index()
)
if not age_mortality_summary.empty:
    age_mortality_summary["tasa_mortalidad"] = (
        age_mortality_summary["fallecidos"] / age_mortality_summary["casos"] * 100
    ).round(2)
    age_mortality_summary = age_mortality_summary.sort_values("tasa_mortalidad", ascending=False)
top_mortality_age_group = (
    age_mortality_summary.iloc[0]["grupo_edad"] if not age_mortality_summary.empty else "Sin dato"
)
top_mortality_age_rate = (
    float(age_mortality_summary.iloc[0]["tasa_mortalidad"]) if not age_mortality_summary.empty else 0.0
)

dept_mortality_summary = (
    prepared_df.groupby("departamento_nom", dropna=False)
    .agg(
        casos=("estado", "size"),
        fallecidos=("estado", lambda s: int(s.astype("string").str.lower().eq("fallecido").sum())),
    )
    .reset_index()
)
dept_mortality_summary = dept_mortality_summary[dept_mortality_summary["casos"] >= 10].copy()
if not dept_mortality_summary.empty:
    dept_mortality_summary["tasa_mortalidad"] = (
        dept_mortality_summary["fallecidos"] / dept_mortality_summary["casos"] * 100
    ).round(2)
    dept_mortality_summary = dept_mortality_summary.sort_values("tasa_mortalidad", ascending=False)
top_mortality_department = (
    dept_mortality_summary.iloc[0]["departamento_nom"] if not dept_mortality_summary.empty else "Sin dato"
)
top_mortality_department_rate = (
    float(dept_mortality_summary.iloc[0]["tasa_mortalidad"]) if not dept_mortality_summary.empty else 0.0
)

sex_fig = build_simple_bar(
    sex_summary,
    x_col="Sexo",
    y_col="Casos",
    title="Distribucion de casos por sexo",
    x_title="Sexo",
    y_title="Numero de casos",
    color="#2563eb",
)
sex_trend_fig = build_multi_line_trend(prepared_df, "sexo", "Evolucion mensual de casos por sexo")
age_share_fig = build_share_donut(
    age_summary,
    label_col="Grupo de edad",
    value_col="Casos",
    title="Participacion relativa por grupo de edad",
)
age_fatality_fig = build_mortality_rate_bar(
    prepared_df,
    group_col="grupo_edad",
    title="Tasa de mortalidad por grupo de edad",
    min_cases=5,
)
department_summary = (
    prepared_df["departamento_nom"]
    .fillna("Sin dato")
    .value_counts()
    .head(8)
    .rename_axis("Departamento")
    .reset_index(name="Casos")
)
department_share_fig = build_share_donut(
    department_summary,
    label_col="Departamento",
    value_col="Casos",
    title="Participacion de los principales departamentos",
)
top_cities_in_leading_department_fig = build_top_city_within_department(prepared_df)
monthly_peak_bar_fig = build_top_months_bar(monthly_cases)
monthly_change_fig = build_monthly_change_chart(monthly_cases)
cases_vs_deaths_combo_fig = build_cases_vs_deaths_combo(monthly_cases, monthly_deaths)
cases_vs_deaths_scatter_fig = build_cases_vs_deaths_scatter(monthly_cases, monthly_deaths)
contagion_share_fig = build_share_donut(
    contagion_summary,
    label_col="Fuente de contagio",
    value_col="Casos",
    title="Participacion por fuente de contagio",
)
location_share_fig = build_share_donut(
    location_summary,
    label_col="Ubicacion",
    value_col="Casos",
    title="Participacion por ubicacion del caso",
)
contagion_trend_fig = build_multi_line_trend(
    prepared_df,
    "fuente_tipo_contagio",
    "Evolucion temporal por fuente de contagio",
)
location_trend_fig = build_multi_line_trend(
    prepared_df,
    "ubicacion",
    "Evolucion temporal por ubicacion del caso",
)
delay_hist_fig = build_delay_distribution(
    prepared_df,
    "dias_sintomas_a_diagnostico",
    "Distribucion del tiempo entre sintomas y diagnostico",
)
delay_age_fig = build_group_metric_bar(
    prepared_df,
    group_col="grupo_edad",
    value_col="dias_sintomas_a_diagnostico",
    title="Promedio de dias a diagnostico por grupo de edad",
    y_title="Dias promedio",
    color="#f97316",
)
delay_department_fig = build_group_metric_bar(
    prepared_df,
    group_col="departamento_nom",
    value_col="dias_sintomas_a_diagnostico",
    title="Departamentos con mayor demora promedio a diagnostico",
    y_title="Dias promedio",
    top_n=8,
    color="#ca8a04",
)
delay_box_fig = build_delay_boxplot(
    prepared_df,
    group_col="grupo_edad",
    value_col="dias_sintomas_a_diagnostico",
    title="Dispersion del tiempo a diagnostico por grupo de edad",
)
deceased_department_fig = build_mortality_rate_bar(
    prepared_df,
    group_col="departamento_nom",
    title="Departamentos con mayor tasa de mortalidad relativa",
    top_n=8,
    min_cases=10,
)
older_adults_fig = build_multi_line_trend(
    prepared_df[prepared_df["grupo_edad"].astype("string") == "60+"].copy()
    if "grupo_edad" in prepared_df.columns
    else prepared_df.copy(),
    "estado",
    "Estados de salud dentro del grupo 60+",
)

render_analysis_metric_grid(
    [
        {"icon": "C", "label": "Casos analizados", "value": f"{total_cases:,}", "sub": "Total de registros"},
        {"icon": "F", "label": "Fallecimientos", "value": f"{total_deaths:,}", "sub": "Total de registros"},
        {"icon": "%", "label": "Tasa de mortalidad", "value": f"{mortality_rate:.2f}%", "sub": "Porcentaje"},
        {"icon": "M", "label": "Metodo de pronostico", "value": result["cases_method"], "sub": "Modelo utilizado"},
        {"icon": "D", "label": "Departamento lider", "value": str(top_department), "sub": "Mayor concentracion"},
        {"icon": "U", "label": "Ciudad lider", "value": str(top_city), "sub": "Mayor concentracion"},
        {"icon": "P", "label": "Mes pico de casos", "value": peak_month_label, "sub": f"+{peak_month_cases:,} casos"},
        {
            "icon": "T",
            "label": "Promedio dias diagnostico",
            "value": "Sin dato" if mean_delay is None else f"{mean_delay:.1f}",
            "sub": "Dias promedio",
        },
    ]
)

st.caption(
    f"Periodo base disponible: {pd.to_datetime(overview['date_min']).strftime('%Y-%m-%d')} a "
    f"{pd.to_datetime(overview['date_max']).strftime('%Y-%m-%d')} | "
    f"Periodo analizado: {pd.to_datetime(start_date).strftime('%Y-%m-%d')} a "
    f"{pd.to_datetime(end_date).strftime('%Y-%m-%d')} | "
    f"Actualizacion del tablero: {pd.to_datetime(result['last_updated']).strftime('%Y-%m-%d %H:%M UTC')}"
)

action_left, action_right = st.columns([0.82, 0.18])
with action_left:
    with st.expander("Metodologia y valor analitico", expanded=False):
        st.markdown(
            """
            - Los datos se consultan desde MongoDB despues de una carga automatizada desde la API de datos abiertos.
            - Las fechas se normalizan a nivel mensual para facilitar comparaciones consistentes.
            - La mortalidad se estima a partir de `fecha_muerte` cuando existe y, en su ausencia, desde el estado `Fallecido`.
            - El pronostico usa el mejor metodo disponible en el entorno y se reporta en pantalla para transparencia metodologica.
            - Los analisis de oportunidad diagnostica se apoyan en `dias_sintomas_a_diagnostico`.
            - Las comparaciones de contagio y ubicacion solo usan registros donde esas variables estan disponibles.
            """
        )
with action_right:
    st.download_button(
        "Descargar analisis filtrado (CSV)",
        data=dataframe_to_csv_bytes(prepared_df),
        file_name="covid_analisis_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )

render_analysis_section_header("Preguntas de negocio que responde este analisis", "?")
render_analysis_question_list(BUSINESS_QUESTIONS)

filters_col, executive_col = st.columns([0.9, 2.1])
with filters_col:
    render_analysis_section_header("Filtros activos", "Y")
    active_filters_html = build_active_filter_cards(
        {
            "Periodo": [f"{pd.to_datetime(start_date).strftime('%Y-%m-%d')} a {pd.to_datetime(end_date).strftime('%Y-%m-%d')}"],
            "Departamentos": selected_departments,
            "Ciudades": selected_cities,
            "Sexo": selected_sexes,
            "Grupo de edad": selected_age_groups,
            "Estado": selected_states_filter,
            "Fuente contagio": selected_contagion_sources,
            "Ubicacion": selected_locations,
            "Tipo recuperacion": selected_recovery_types,
        }
    )
    st.markdown(active_filters_html, unsafe_allow_html=True)

with executive_col:
    render_analysis_section_header("Lectura ejecutiva del periodo", "B")
    render_analysis_notes(
        [
            f"El periodo filtrado concentra <strong>{total_cases:,} casos</strong> y su mayor pico se observa en <strong>{peak_month_label}</strong> con <strong>{peak_month_cases:,} registros</strong>.",
            f"La concentracion territorial se lidera desde <strong>{top_department}</strong> y, a nivel urbano, la ciudad con mas registros es <strong>{top_city}</strong>.",
            f"La tasa de mortalidad del subconjunto analizado es <strong>{mortality_rate:.2f}%</strong> y los estados comparados actualmente son <strong>{', '.join(selected_trend_states)}</strong>.",
            f"El grupo etario con mayor participacion es <strong>{leading_age_group}</strong> con <strong>{leading_age_group_cases:,} casos</strong>.",
        ]
    )

render_analysis_section_header("Selecciona una pregunta para responderla con los filtros actuales", "Q")
selected_question_label = st.radio(
    "Pregunta activa",
    options=list(QUESTION_OPTIONS.keys()) + ["Datos base"],
    horizontal=True,
    label_visibility="collapsed",
)

forecast_enabled_questions = {"Meses pico", "Casos vs mortalidad"}
if selected_question_label in forecast_enabled_questions:
    st.info(
        f"Esta pregunta usa el filtro **Meses a pronosticar**. El horizonte actual del pronostico es de **{forecast_periods} meses**."
    )
else:
    st.caption(
        f"El filtro `Meses a pronosticar` no cambia esta pregunta. Solo impacta `Meses pico` y `Casos vs mortalidad`. Valor actual: {forecast_periods} meses."
    )

if selected_question_label != "Datos base":
    st.markdown(
        f'<div class="section-chip">Pregunta activa</div><h3 style="margin-top:0;">{QUESTION_OPTIONS[selected_question_label]}</h3>',
        unsafe_allow_html=True,
    )

if selected_question_label == "Meses pico":
    render_answer_box(
        "Respuesta principal",
        f"Los casos se concentran sobre todo en <strong>{peak_month_label}</strong>, que registra "
        f"<strong>{peak_month_cases:,} casos</strong> dentro del filtro actual. Ademas, el mayor salto "
        f"mensual se observa en <strong>{largest_growth_month_label}</strong> con una variacion de "
        f"<strong>{largest_growth_value:,} casos</strong>, lo que sugiere un periodo de aceleracion clara.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(result["fig_cases"], width="stretch")
    with top_row_right:
        st.plotly_chart(monthly_peak_bar_fig, width="stretch")
    st.plotly_chart(monthly_change_fig, width="stretch")
    st.caption(
        "Esta pregunta se responde desde tendencia general, ranking de meses pico y cambio mes a mes. El tramo futuro cambia segun el filtro de pronostico."
    )

elif selected_question_label == "Territorio":
    render_answer_box(
        "Respuesta principal",
        f"La mayor concentracion territorial del filtro actual esta en <strong>{top_department}</strong>, "
        f"mientras que la ciudad con mas registros es <strong>{top_city}</strong>. Esto indica que la carga "
        f"del conjunto analizado no esta distribuida de forma uniforme, sino que se concentra en unos pocos territorios lideres.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(result["fig_top_departments"], width="stretch")
    with top_row_right:
        st.plotly_chart(result["fig_cases_by_city"], width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(result["fig_cases_by_department"], width="stretch")
    with bottom_right:
        st.plotly_chart(department_share_fig, width="stretch")
    st.plotly_chart(top_cities_in_leading_department_fig, width="stretch")
    st.caption(
        "Aqui se combinan evolucion territorial, ranking de ciudades, peso relativo departamental y detalle del territorio dominante."
    )

elif selected_question_label == "Edad":
    render_answer_box(
        "Respuesta principal",
        f"El grupo con mayor participacion es <strong>{leading_age_group}</strong> con "
        f"<strong>{leading_age_group_cases:,} casos</strong>, seguido por <strong>{second_age_group}</strong> "
        f"con <strong>{second_age_group_cases:,} casos</strong>. En severidad relativa, el grupo "
        f"<strong>{top_mortality_age_group}</strong> presenta la tasa de mortalidad mas alta del filtro actual "
        f"con <strong>{top_mortality_age_rate:.2f}%</strong>.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(result["fig_age"], width="stretch")
    with top_row_right:
        st.plotly_chart(age_share_fig, width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(age_fatality_fig, width="stretch")
    with bottom_right:
        st.dataframe(age_summary, use_container_width=True, hide_index=True)
    st.caption(
        "Aqui se responde la pregunta desde composicion temporal, participacion relativa y mortalidad relativa por grupo etario."
    )

elif selected_question_label == "Sexo":
    render_answer_box(
        "Respuesta principal",
        f"El sexo con mayor volumen de casos es <strong>{top_sex}</strong> con "
        f"<strong>{top_sex_cases:,} registros</strong>. La interpretacion completa debe contrastar este volumen "
        f"con la distribucion de fallecimientos y con la evolucion temporal, porque el liderazgo en casos no siempre implica mayor severidad.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(sex_fig, width="stretch")
    with top_row_right:
        st.plotly_chart(result["fig_gender_distribution_deceased"], width="stretch")
    st.plotly_chart(sex_trend_fig, width="stretch")
    st.caption(
        "Aqui se responde la pregunta desde volumen total, fallecimientos por sexo y evolucion temporal por categoria."
    )

elif selected_question_label == "Casos vs mortalidad":
    render_answer_box(
        "Respuesta principal",
        f"En el filtro actual se observan <strong>{total_cases:,} casos</strong> y "
        f"<strong>{total_deaths:,} fallecimientos</strong>, para una tasa de mortalidad de "
        f"<strong>{mortality_rate:.2f}%</strong>. La lectura conjunta permite evaluar si los meses con mas casos "
        f"tambien empujan aumentos en mortalidad o si ambas curvas se desacoplan.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(result["fig_cases"], width="stretch")
    with top_row_right:
        st.plotly_chart(result["fig_mortality"], width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(cases_vs_deaths_combo_fig, width="stretch")
    with bottom_right:
        st.plotly_chart(cases_vs_deaths_scatter_fig, width="stretch")
    st.caption(
        "Aqui se responde la pregunta desde dos series separadas, una vista conjunta y la relacion mensual entre ambas variables."
    )

elif selected_question_label == "Severidad":
    render_answer_box(
        "Respuesta principal",
        f"La severidad del filtro actual se concentra especialmente en <strong>{top_mortality_department}</strong>, "
        f"que muestra la tasa de mortalidad relativa mas alta con <strong>{top_mortality_department_rate:.2f}%</strong>, "
        f"y en el grupo etario <strong>{top_mortality_age_group}</strong>, que alcanza "
        f"<strong>{top_mortality_age_rate:.2f}%</strong>. Esto sugiere priorizar territorios y poblaciones con mayor riesgo relativo.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(result["fig_health_state_trends"], width="stretch")
    with top_row_right:
        st.plotly_chart(deceased_department_fig, width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(older_adults_fig, width="stretch")
    with bottom_right:
        st.plotly_chart(age_fatality_fig, width="stretch")
    st.caption(
        "Aqui se combinan estados de salud, mortalidad relativa por departamento y focos de severidad en adultos mayores y grupos de edad."
    )

elif selected_question_label == "Oportunidad diagnostica":
    render_answer_box(
        "Respuesta principal",
        f"El tiempo promedio entre sintomas y diagnostico es "
        f"<strong>{'Sin dato' if mean_delay is None else f'{mean_delay:.1f} dias'}</strong> y la mediana es "
        f"<strong>{'Sin dato' if median_delay is None else f'{median_delay:.1f} dias'}</strong>. "
        f"Cuando esta brecha aumenta, el filtro actual sugiere una menor oportunidad diagnostica y posibles diferencias entre grupos de edad y departamentos.",
    )
    st.markdown(
        f"""
        <div class="kpi-note">
            El tiempo promedio entre sintomas y diagnostico en el filtro actual es
            <strong>{"Sin dato" if mean_delay is None else f"{mean_delay:.1f} dias"}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(delay_hist_fig, width="stretch")
    with top_row_right:
        st.plotly_chart(delay_age_fig, width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(delay_department_fig, width="stretch")
    with bottom_right:
        st.plotly_chart(delay_box_fig, width="stretch")
    st.caption(
        "Aqui se responde la pregunta desde distribucion general, promedio por grupo etario, comparacion territorial y dispersion de los tiempos a diagnostico."
    )

elif selected_question_label == "Contagio y atencion":
    render_answer_box(
        "Respuesta principal",
        f"La fuente de contagio dominante en el filtro actual es <strong>{top_contagion}</strong> con "
        f"<strong>{top_contagion_cases:,} casos</strong>, mientras que la ubicacion mas frecuente es "
        f"<strong>{top_location}</strong> con <strong>{top_location_cases:,} registros</strong>. "
        f"Esto permite evaluar si el comportamiento del brote se explica principalmente por contagio comunitario y atencion domiciliaria u otro patron.",
    )
    top_row_left, top_row_right = st.columns(2)
    with top_row_left:
        st.plotly_chart(contagion_share_fig, width="stretch")
    with top_row_right:
        st.plotly_chart(location_share_fig, width="stretch")
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(contagion_trend_fig, width="stretch")
    with bottom_right:
        st.plotly_chart(location_trend_fig, width="stretch")
    st.caption(
        "Aqui se responde la pregunta desde participacion relativa y evolucion temporal de la fuente de contagio y la ubicacion del caso."
    )

else:
    st.markdown(
        '<div class="section-chip">Respaldo</div><h3 style="margin-top:0;">Series y tablas base del analisis</h3>',
        unsafe_allow_html=True,
    )
    base_left, base_right = st.columns(2)
    with base_left:
        st.subheader("Casos mensuales")
        st.dataframe(
            monthly_cases.rename(columns={"ds": "Mes", "y": "Casos"}),
            use_container_width=True,
        )
    with base_right:
        st.subheader("Mortalidad mensual")
        st.dataframe(
            monthly_deaths.rename(columns={"ds": "Mes", "y": "Fallecimientos"}),
            use_container_width=True,
        )
