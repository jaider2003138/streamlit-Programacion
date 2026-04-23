"""
Script para actualizar la coleccion desde la API sin intervencion manual.

Pensado para ejecutarse con Task Scheduler, cron o cualquier servicio externo.
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from api_service import fetch_data, fetch_total_count
from mongo_db import save_data

load_dotenv()


def str_to_bool(value: str | None, default: bool = False) -> bool:
    """Convierte texto a bool usando convenciones comunes."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Descarga datos desde la API y actualiza MongoDB automaticamente."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Descarga el conjunto completo del endpoint mediante paginacion.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Numero maximo de registros a descargar cuando no se usa --full.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("AUTO_UPDATE_BATCH_SIZE", "5000")),
        help="Tamano de lote para descargas paginadas.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=os.getenv("COLLECTION_NAME", "datos_api"),
        help="Coleccion destino en MongoDB.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    api_url = os.getenv("API_URL", "https://www.datos.gov.co/resource/gt2j-8ykr.json")
    env_full = str_to_bool(os.getenv("AUTO_UPDATE_FULL_DATA"), default=False)
    env_limit = os.getenv("AUTO_UPDATE_LIMIT")

    full_download = args.full or env_full
    limit = None if full_download else args.limit
    if limit is None and not full_download and env_limit:
        limit = int(env_limit)
    if limit is None and not full_download:
        limit = 1000

    print("[auto_update] Iniciando actualizacion automatica...")
    print(f"[auto_update] API origen: {api_url}")
    print(f"[auto_update] Coleccion destino: {args.collection}")

    total_available = fetch_total_count(api_url)
    if total_available is not None:
        print(f"[auto_update] Registros reportados por la fuente: {total_available}")

    records = fetch_data(
        api_url,
        limit=None if full_download else limit,
        batch_size=args.batch_size,
    )
    if not records:
        print("[auto_update] No se obtuvieron registros. La actualizacion no se completo.")
        return 1

    inserted = save_data(
        args.collection,
        records,
        refresh_context="scheduled-script",
        records_requested=(None if full_download else limit) or len(records),
    )
    if inserted <= 0:
        print("[auto_update] No se insertaron registros en MongoDB.")
        return 1

    print(f"[auto_update] Actualizacion completada. Documentos insertados: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
