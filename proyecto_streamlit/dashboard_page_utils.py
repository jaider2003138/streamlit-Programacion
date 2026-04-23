"""
Utilidades compartidas para las paginas de analisis y graficos.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from covid_dataframe_utils import prepare_clean_dataframe
from mongo_db import load_data


@st.cache_data(ttl=120, show_spinner="Cargando datos limpios desde MongoDB...")
def load_collection_dataframe(collection_name: str) -> pd.DataFrame:
    """Carga la coleccion de MongoDB y la transforma en DataFrame."""
    records = load_data(collection_name)
    return pd.DataFrame(records) if records else pd.DataFrame()


def prepare_dashboard_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara el DataFrame para filtros y graficas."""
    return prepare_clean_dataframe(df)


def apply_common_filters(
    df: pd.DataFrame,
    start_date: object | None = None,
    end_date: object | None = None,
    departments: list[str] | None = None,
    cities: list[str] | None = None,
    sexes: list[str] | None = None,
    age_groups: list[str] | None = None,
    states: list[str] | None = None,
    contagion_sources: list[str] | None = None,
    locations: list[str] | None = None,
    recovery_types: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica los filtros generales seleccionados desde la barra lateral."""
    filtered = df.copy()

    if start_date is not None:
        start_ts = pd.to_datetime(start_date, errors="coerce")
        if not pd.isna(start_ts):
            filtered = filtered[filtered["mes_reporte_fecha"] >= start_ts]

    if end_date is not None:
        end_ts = pd.to_datetime(end_date, errors="coerce")
        if not pd.isna(end_ts):
            filtered = filtered[filtered["mes_reporte_fecha"] <= end_ts]

    if departments:
        filtered = filtered[filtered["departamento_nom"].isin(departments)]
    if cities:
        filtered = filtered[filtered["ciudad_municipio_nom"].isin(cities)]
    if sexes:
        filtered = filtered[filtered["sexo"].isin(sexes)]
    if age_groups:
        filtered = filtered[filtered["grupo_edad"].isin(age_groups)]
    if states:
        filtered = filtered[filtered["estado"].isin(states)]
    if contagion_sources and "fuente_tipo_contagio" in filtered.columns:
        filtered = filtered[filtered["fuente_tipo_contagio"].isin(contagion_sources)]
    if locations and "ubicacion" in filtered.columns:
        filtered = filtered[filtered["ubicacion"].isin(locations)]
    if recovery_types and "tipo_recuperacion" in filtered.columns:
        filtered = filtered[filtered["tipo_recuperacion"].isin(recovery_types)]

    return filtered.reset_index(drop=True)


def get_filter_options(df: pd.DataFrame) -> dict[str, object]:
    """Construye opciones limpias para controles de filtros."""
    report_dates = df["mes_reporte_fecha"].dropna().sort_values()
    min_date = report_dates.min().date() if not report_dates.empty else None
    max_date = report_dates.max().date() if not report_dates.empty else None

    return {
        "min_date": min_date,
        "max_date": max_date,
        "departments": sorted(df["departamento_nom"].dropna().astype(str).unique().tolist()),
        "cities": sorted(df["ciudad_municipio_nom"].dropna().astype(str).unique().tolist()),
        "sexes": sorted(df["sexo"].dropna().astype(str).unique().tolist()),
        "age_groups": sorted(df["grupo_edad"].dropna().astype(str).unique().tolist()),
        "states": sorted(df["estado"].dropna().astype(str).unique().tolist()),
        "contagion_sources": sorted(
            df["fuente_tipo_contagio"].dropna().astype(str).unique().tolist()
        )
        if "fuente_tipo_contagio" in df.columns
        else [],
        "locations": sorted(df["ubicacion"].dropna().astype(str).unique().tolist())
        if "ubicacion" in df.columns
        else [],
        "recovery_types": sorted(
            df["tipo_recuperacion"].dropna().astype(str).unique().tolist()
        )
        if "tipo_recuperacion" in df.columns
        else [],
    }


def get_default_trend_states(df: pd.DataFrame) -> list[str]:
    """Selecciona 3 estados utiles como valor inicial para la comparacion temporal."""
    preferred_order = ["Leve", "Grave", "Fallecido", "Moderado", "Asintomatico"]
    available_states = df["estado"].dropna().astype(str)
    available_set = set(available_states.unique())

    selected = [state for state in preferred_order if state in available_set]
    if len(selected) < 3:
        for state in available_states.value_counts().index.tolist():
            if state not in selected:
                selected.append(state)
            if len(selected) == 3:
                break

    return selected[:3]


def get_dataset_overview(df: pd.DataFrame) -> dict[str, object]:
    """Construye metadatos utiles para cabeceras y contexto."""
    overview: dict[str, object] = {
        "rows": len(df),
        "columns": len(df.columns),
        "date_min": None,
        "date_max": None,
        "departments": int(df["departamento_nom"].nunique(dropna=True)),
        "cities": int(df["ciudad_municipio_nom"].nunique(dropna=True)),
        "states": int(df["estado"].nunique(dropna=True)),
        "source": os.getenv("API_URL", "https://www.datos.gov.co/resource/gt2j-8ykr.json"),
    }

    dates = df["mes_reporte_fecha"].dropna().sort_values()
    if not dates.empty:
        overview["date_min"] = dates.min()
        overview["date_max"] = dates.max()

    return overview


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a CSV UTF-8 listo para descarga."""
    export_df = df.copy()
    for column in export_df.columns:
        if pd.api.types.is_datetime64_any_dtype(export_df[column]):
            export_df[column] = export_df[column].astype("string")
    return export_df.to_csv(index=False).encode("utf-8")
