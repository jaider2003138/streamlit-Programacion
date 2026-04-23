"""
data_cleaning.py
Rutinas de limpieza y estandarizacion para el dataset COVID.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any
import unicodedata

import pandas as pd


COVID_REQUIRED_COLUMNS = {
    "fecha_reporte_web",
    "id_de_caso",
    "departamento_nom",
    "ciudad_municipio_nom",
    "edad",
    "sexo",
    "estado",
}

COVID_RENAME_MAP = {
    "fecha_de_notificaci_n": "fecha_de_notificacion",
    "per_etn_": "per_etnica",
    "nom_grupo_": "grupo_poblacional",
}

DROP_COLUMNS = {"_id", "unidad_medida"}
STRING_NA_VALUES = {"", "N/A", "NA", "NAN", "NONE", "NULL", "SIN DATO", "NO APLICA"}
DATE_COLUMNS = {
    "fecha_reporte_web",
    "fecha_de_notificacion",
    "fecha_inicio_sintomas",
    "fecha_diagnostico",
    "fecha_recuperado",
    "fecha_muerte",
}
IDENTIFIER_COLUMNS = {"id_de_caso", "departamento", "ciudad_municipio"}

SEX_MAP = {
    "M": "Masculino",
    "F": "Femenino",
}

STATE_MAP = {
    "LEVE": "Leve",
    "MODERADO": "Moderado",
    "GRAVE": "Grave",
    "FALLECIDO": "Fallecido",
    "ASINTOMATICO": "Asintomatico",
    "ASINTOMÁTICO": "Asintomatico",
}

RECOVERED_MAP = {
    "RECUPERADO": "Recuperado",
    "FALLECIDO": "Fallecido",
}

LOCATION_MAP = {
    "CASA": "Casa",
    "HOSPITAL": "Hospital",
    "HOSPITALIZADO": "Hospital",
    "UCI": "UCI",
    "FALLECIDO": "Fallecido",
}

CONTAGION_MAP = {
    "COMUNITARIA": "Comunitaria",
    "RELACIONADO": "Relacionado",
    "EN ESTUDIO": "En estudio",
    "IMPORTADO": "Importado",
}

DEPARTMENT_MAP = {
    "AMAZONAS": "Amazonas",
    "ANTIOQUIA": "Antioquia",
    "ARAUCA": "Arauca",
    "ATLANTICO": "Atlantico",
    "ATLÁNTICO": "Atlantico",
    "BARRANQUILLA": "Barranquilla",
    "BOGOTA": "Bogota",
    "BOGOTÁ": "Bogota",
    "BOGOTA D.C.": "Bogota",
    "BOGOTA D C": "Bogota",
    "BOGOTA DC": "Bogota",
    "BOLIVAR": "Bolivar",
    "BOLÍVAR": "Bolivar",
    "BOYACA": "Boyaca",
    "BOYACÁ": "Boyaca",
    "CALDAS": "Caldas",
    "CAQUETA": "Caqueta",
    "CAQUETÁ": "Caqueta",
    "CARTAGENA": "Cartagena",
    "CASANARE": "Casanare",
    "CAUCA": "Cauca",
    "CESAR": "Cesar",
    "CHOCO": "Choco",
    "CHOCÓ": "Choco",
    "CORDOBA": "Cordoba",
    "CÓRDOBA": "Cordoba",
    "CUNDINAMARCA": "Cundinamarca",
    "GUAINIA": "Guainia",
    "GUAINÍA": "Guainia",
    "GUAINIA ": "Guainia",
    "GUAVIARE": "Guaviare",
    "HUILA": "Huila",
    "LA GUAJIRA": "La Guajira",
    "MAGDALENA": "Magdalena",
    "META": "Meta",
    "NARIÑO": "Narino",
    "NARINO": "Narino",
    "NORTE DE SANTANDER": "Norte De Santander",
    "PUTUMAYO": "Putumayo",
    "QUINDIO": "Quindio",
    "QUINDÍO": "Quindio",
    "RISARALDA": "Risaralda",
    "SAN ANDRES": "San Andres",
    "SAN ANDRÉS": "San Andres",
    "SANTA MARTA D.E.": "Santa Marta",
    "SANTANDER": "Santander",
    "SUCRE": "Sucre",
    "TOLIMA": "Tolima",
    "VALLE": "Valle",
    "VALLE DEL CAUCA": "Valle Del Cauca",
    "VAUPES": "Vaupes",
    "VAUPÉS": "Vaupes",
    "VICHADA": "Vichada",
}

CITY_MAP = {
    "BOGOTA": "Bogota",
    "BOGOTÁ": "Bogota",
    "BOGOTA D.C.": "Bogota",
    "BOGOTA DC": "Bogota",
    "MEDELLIN": "Medellin",
    "MEDELLÍN": "Medellin",
    "IBAGUE": "Ibague",
    "IBAGUÉ": "Ibague",
    "CALI": "Cali",
    "BARRANQUILLA": "Barranquilla",
    "CARTAGENA": "Cartagena",
    "BUCARAMANGA": "Bucaramanga",
    "SANTA MARTA": "Santa Marta",
    "SAN ANDRES": "San Andres",
    "SAN ANDRÉS": "San Andres",
}


def detect_covid_dataset(records: list[dict[str, Any]]) -> bool:
    """Indica si el conjunto de registros corresponde al dataset COVID."""
    if not records:
        return False
    keys = set(records[0].keys())
    renamed_keys = {COVID_RENAME_MAP.get(key, key) for key in keys}
    return COVID_REQUIRED_COLUMNS.issubset(renamed_keys)


def clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aplica una limpieza apropiada segun el tipo de dataset detectado."""
    if detect_covid_dataset(records):
        return clean_covid_records(records)
    return records


def clean_covid_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Limpia el dataset de casos COVID proveniente de datos.gov.co."""
    cleaned_records: list[dict[str, Any]] = []

    for record in records:
        cleaned: dict[str, Any] = {}

        for key, value in record.items():
            if key in DROP_COLUMNS:
                continue

            target_key = COVID_RENAME_MAP.get(key, key)
            if target_key in DROP_COLUMNS:
                continue

            cleaned[target_key] = _clean_generic_value(target_key, value)

        cleaned["grupo_edad"] = _compute_age_group(cleaned.get("edad"))
        cleaned["anio_reporte"] = _extract_year(cleaned.get("fecha_reporte_web"))
        cleaned["mes_reporte"] = _extract_month(cleaned.get("fecha_reporte_web"))
        cleaned["anio_diagnostico"] = _extract_year(cleaned.get("fecha_diagnostico"))
        cleaned["mes_diagnostico"] = _extract_month(cleaned.get("fecha_diagnostico"))
        cleaned["dias_sintomas_a_diagnostico"] = _date_diff_days(
            cleaned.get("fecha_inicio_sintomas"),
            cleaned.get("fecha_diagnostico"),
        )
        cleaned["dias_diagnostico_a_recuperacion"] = _date_diff_days(
            cleaned.get("fecha_diagnostico"),
            cleaned.get("fecha_recuperado"),
        )
        cleaned["dias_diagnostico_a_muerte"] = _date_diff_days(
            cleaned.get("fecha_diagnostico"),
            cleaned.get("fecha_muerte"),
        )

        cleaned_records.append(cleaned)

    return cleaned_records


def _clean_generic_value(column: str, value: Any) -> Any:
    """Normaliza un valor individual segun la columna a la que pertenece."""
    if value is None:
        return None

    if isinstance(value, str):
        value = " ".join(value.strip().split())
        if value.upper() in STRING_NA_VALUES:
            return None

    if column in DATE_COLUMNS:
        return _parse_datetime(value)

    if column == "edad":
        numeric = pd.to_numeric(value, errors="coerce")
        return None if pd.isna(numeric) else int(numeric)

    if column in IDENTIFIER_COLUMNS:
        return None if pd.isna(value) else str(value).strip()

    if column == "sexo":
        normalized = _normalize_text(value)
        return SEX_MAP.get(normalized, _smart_title(value))

    if column == "estado":
        normalized = _normalize_text(value)
        return STATE_MAP.get(normalized, _smart_title(value))

    if column == "recuperado":
        normalized = _normalize_text(value)
        return RECOVERED_MAP.get(normalized, _smart_title(value))

    if column == "ubicacion":
        normalized = _normalize_text(value)
        return LOCATION_MAP.get(normalized, _smart_title(value))

    if column == "fuente_tipo_contagio":
        normalized = _normalize_text(value)
        return CONTAGION_MAP.get(normalized, _smart_title(value))

    if column == "departamento_nom":
        normalized = _normalize_text(value)
        return DEPARTMENT_MAP.get(normalized, _smart_title(value))

    if column == "ciudad_municipio_nom":
        normalized = _normalize_text(value)
        return CITY_MAP.get(normalized, _smart_title(value))

    if column in {"tipo_recuperacion", "per_etnica", "grupo_poblacional", "pais_viajo_1_nom"}:
        return _smart_title(value)

    if isinstance(value, str):
        return value

    return value


def _parse_datetime(value: Any) -> datetime | None:
    """Convierte un valor a datetime de Python si es valido."""
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.to_pydatetime()


def _normalize_text(value: Any) -> str:
    """Normaliza texto para comparaciones robustas."""
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.replace(".", " ").split())


def _smart_title(value: Any) -> str | None:
    """Aplica formato legible a categorias de texto."""
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None
    if text.upper() in STRING_NA_VALUES:
        return None

    special_cases = {
        "UCI": "UCI",
        "IPS": "IPS",
        "EPS": "EPS",
        "N/A": None,
    }
    normalized = _normalize_text(text)
    if normalized in special_cases:
        return special_cases[normalized]

    return text.title()


def _compute_age_group(age_value: Any) -> str | None:
    """Agrupa edades en rangos interpretables para el analisis."""
    if age_value is None or pd.isna(age_value):
        return None

    age = int(age_value)
    if age < 18:
        return "0-17"
    if age < 30:
        return "18-29"
    if age < 45:
        return "30-44"
    if age < 60:
        return "45-59"
    return "60+"


def _extract_year(date_value: Any) -> int | None:
    """Extrae el anio de una fecha."""
    if not date_value:
        return None
    parsed = pd.to_datetime(date_value, errors="coerce")
    return None if pd.isna(parsed) else int(parsed.year)


def _extract_month(date_value: Any) -> str | None:
    """Extrae el mes de una fecha en formato YYYY-MM."""
    if not date_value:
        return None
    parsed = pd.to_datetime(date_value, errors="coerce")
    return None if pd.isna(parsed) else parsed.strftime("%Y-%m")


def _date_diff_days(start_value: Any, end_value: Any) -> int | None:
    """Calcula diferencia de dias entre dos fechas si ambas son validas."""
    if not start_value or not end_value:
        return None

    start = pd.to_datetime(start_value, errors="coerce")
    end = pd.to_datetime(end_value, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return None

    diff = (end - start).days
    return diff if diff >= 0 else None


def summarize_category(series: pd.Series, top_n: int = 10) -> list[tuple[str, int]]:
    """Devuelve un resumen compacto de una serie categorica."""
    counts = series.fillna("Sin dato").astype(str).value_counts().head(top_n)
    return [(index, int(value)) for index, value in counts.items()]


def count_null_like_values(values: Iterable[Any]) -> int:
    """Cuenta valores que la limpieza convertira a nulo."""
    total = 0
    for value in values:
        if value is None:
            total += 1
        elif isinstance(value, str) and value.strip().upper() in STRING_NA_VALUES:
            total += 1
    return total
