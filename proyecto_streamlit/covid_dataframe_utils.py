"""
Utilidades de preparacion y validacion de datos para el dashboard COVID.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "fecha_reporte_web",
    "departamento_nom",
    "ciudad_municipio_nom",
    "edad",
    "sexo",
    "estado",
}


class DatasetValidationError(ValueError):
    """Error legible para dataset incompleto o mal formado."""


def require_columns(df: pd.DataFrame, required_columns: set[str], context: str) -> None:
    """Valida columnas requeridas para una operacion puntual."""
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise DatasetValidationError(
            f"Faltan columnas obligatorias para {context}: {', '.join(missing)}"
        )


def prepare_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Valida y prepara un DataFrame ya cargado en memoria para el dashboard."""
    if df.empty:
        raise DatasetValidationError("El DataFrame esta vacio.")

    prepared = ensure_required_columns(df.copy())
    prepared = ensure_temporal_columns(prepared)
    prepared = ensure_age_group_column(prepared)
    prepared = normalize_state_column(prepared)
    return prepared


def load_clean_dataset(path: str | Path) -> pd.DataFrame:
    """Carga un dataset limpio desde CSV o JSON y valida columnas obligatorias."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {dataset_path}")

    suffix = dataset_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(dataset_path)
    elif suffix == ".json":
        df = pd.read_json(dataset_path)
    else:
        raise DatasetValidationError(f"Formato no soportado: {suffix}. Usa CSV o JSON.")

    if df.empty:
        raise DatasetValidationError("El archivo esta vacio.")

    return prepare_clean_dataframe(df)


def ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Valida que existan las columnas minimas necesarias."""
    missing = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing:
        raise DatasetValidationError(
            "Faltan columnas obligatorias en el dataset limpio: " + ", ".join(missing)
        )
    return df.copy()


def ensure_temporal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte fechas de forma robusta y construye columnas temporales si faltan."""
    date_columns = ["fecha_reporte_web", "fecha_diagnostico", "fecha_muerte"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "mes_reporte" not in df.columns:
        if "fecha_reporte_web" not in df.columns:
            raise DatasetValidationError(
                "Se requiere `mes_reporte` o `fecha_reporte_web` para el analisis temporal."
            )
        df["mes_reporte"] = df["fecha_reporte_web"].dt.to_period("M").astype(str)

    if "anio_reporte" not in df.columns and "fecha_reporte_web" in df.columns:
        df["anio_reporte"] = df["fecha_reporte_web"].dt.year

    if "mes_diagnostico" not in df.columns and "fecha_diagnostico" in df.columns:
        df["mes_diagnostico"] = df["fecha_diagnostico"].dt.to_period("M").astype(str)

    if "anio_diagnostico" not in df.columns and "fecha_diagnostico" in df.columns:
        df["anio_diagnostico"] = df["fecha_diagnostico"].dt.year

    df["mes_reporte_fecha"] = pd.to_datetime(df["mes_reporte"], errors="coerce")
    if df["mes_reporte_fecha"].isna().all():
        raise DatasetValidationError(
            "La columna `mes_reporte` no pudo convertirse a fechas validas."
        )

    return df


def ensure_age_group_column(df: pd.DataFrame) -> pd.DataFrame:
    """Crea grupo_edad si no existe."""
    if "grupo_edad" in df.columns:
        return df

    edad = pd.to_numeric(df["edad"], errors="coerce")
    bins = [-1, 17, 29, 44, 59, 200]
    labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
    df["grupo_edad"] = pd.cut(edad, bins=bins, labels=labels)
    df["grupo_edad"] = df["grupo_edad"].astype("string")
    return df


def normalize_state_column(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la columna estado para el analisis de mortalidad."""
    df["estado"] = df["estado"].astype("string").str.strip()
    return df


def prepare_monthly_series(
    df: pd.DataFrame,
    date_column: str = "mes_reporte",
    count_column_name: str = "casos",
) -> pd.DataFrame:
    """Agrupa el dataset por mes y cuenta registros."""
    if date_column not in df.columns:
        raise DatasetValidationError(f"No existe la columna temporal `{date_column}`.")

    series = (
        df.groupby(date_column, dropna=False)
        .size()
        .reset_index(name=count_column_name)
        .rename(columns={date_column: "ds", count_column_name: "y"})
    )
    series["ds"] = pd.to_datetime(series["ds"], errors="coerce")
    series = series.dropna(subset=["ds"]).sort_values("ds").reset_index(drop=True)

    if series.empty:
        raise DatasetValidationError("No fue posible construir la serie temporal mensual.")

    return series


def prepare_mortality_series(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la serie temporal mensual de mortalidad."""
    if "fecha_muerte" in df.columns:
        death_df = df[df["fecha_muerte"].notna()].copy()
        if not death_df.empty:
            death_df["mes_muerte"] = death_df["fecha_muerte"].dt.to_period("M").astype(str)
            return prepare_monthly_series(
                death_df,
                date_column="mes_muerte",
                count_column_name="fallecimientos",
            )

    death_df = df[df["estado"].astype("string").str.lower() == "fallecido"].copy()
    return prepare_monthly_series(
        death_df,
        date_column="mes_reporte",
        count_column_name="fallecimientos",
    )
