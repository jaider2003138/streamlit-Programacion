"""
api_service.py
Modulo para consumir la API publica de datos abiertos de Colombia.
"""

from __future__ import annotations

import requests
from dotenv import load_dotenv

load_dotenv()


def fetch_total_count(url: str) -> int | None:
    """Consulta el total de registros del recurso Socrata."""
    try:
        response = requests.get(
            url,
            params={"$select": "count(*)"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return int(data[0]["count"])
    except Exception as e:
        print(f"[api_service] No se pudo consultar el total del recurso: {e}")
        return None


def fetch_data(url: str, limit: int | None = 1000, batch_size: int = 5000) -> list[dict]:
    """
    Consume la API publica y retorna una lista de registros.

    Args:
        url: Endpoint de la API (formato Socrata / datos.gov.co).
        limit: Numero maximo de registros a obtener. Si es None, descarga todo.
        batch_size: Tamano del lote por solicitud cuando se pagina.

    Returns:
        Lista de dicts con los registros, o lista vacia si ocurre un error.
    """
    try:
        if limit is not None and limit <= batch_size:
            response = requests.get(url, params={"$limit": limit}, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"[api_service] {len(data)} registros obtenidos desde {url}")
            return data

        records: list[dict] = []
        offset = 0
        remaining = limit

        while True:
            current_limit = batch_size if remaining is None else min(batch_size, remaining)
            params = {"$limit": current_limit, "$offset": offset}
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            chunk = response.json()

            if not chunk:
                break

            records.extend(chunk)
            offset += len(chunk)

            if remaining is not None:
                remaining -= len(chunk)
                if remaining <= 0:
                    break

            if len(chunk) < current_limit:
                break

        print(f"[api_service] {len(records)} registros obtenidos desde {url}")
        return records
    except requests.exceptions.HTTPError as e:
        print(f"[api_service] Error HTTP al consumir la API: {e}")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"[api_service] Error de conexion: {e}")
        return []
    except requests.exceptions.Timeout:
        print("[api_service] La solicitud supero el tiempo de espera.")
        return []
    except Exception as e:
        print(f"[api_service] Error inesperado: {e}")
        return []
