"""
mongo_db.py
Modulo de acceso a MongoDB Atlas.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from data_cleaning import clean_records

load_dotenv()

METADATA_COLLECTION = "_system_metadata"
DEFAULT_INSERT_BATCH_SIZE = 5000


def _get_connection_settings() -> tuple[str, str, str, str]:
    """Lee y valida las variables de entorno necesarias para MongoDB."""
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASSWORD")
    host = os.getenv("MONGO_HOST")
    db_name = os.getenv("MONGO_DB")

    if not all([user, password, host, db_name]):
        raise ValueError(
            "Faltan variables de entorno: MONGO_USER, MONGO_PASSWORD, "
            "MONGO_HOST o MONGO_DB"
        )

    return user, password, host, db_name


@lru_cache(maxsize=1)
def _get_mongo_client(uri: str) -> MongoClient:
    """Crea un cliente reutilizable para evitar resolver DNS en cada llamada."""
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def get_db():
    """
    Conecta a MongoDB Atlas usando variables de entorno.

    Variables requeridas: MONGO_USER, MONGO_PASSWORD, MONGO_HOST, MONGO_DB.

    Returns:
        Objeto database de PyMongo, o None si la conexion falla.
    """
    try:
        user, password, host, db_name = _get_connection_settings()
        safe_user = quote_plus(user)
        safe_password = quote_plus(password)
        uri = (
            f"mongodb+srv://{safe_user}:{safe_password}@{host}/{db_name}"
            "?retryWrites=true&w=majority"
        )
        client = _get_mongo_client(uri)
        client.admin.command("ping")
        print("[mongo_db] Conexion exitosa a MongoDB Atlas.")
        return client[db_name]
    except ConnectionFailure as e:
        _get_mongo_client.cache_clear()
        print(f"[mongo_db] No se pudo conectar a MongoDB: {e}")
        return None
    except ValueError as e:
        print(f"[mongo_db] Error de configuracion: {e}")
        return None
    except Exception as e:
        _get_mongo_client.cache_clear()
        print(f"[mongo_db] Error inesperado al conectar: {e}")
        return None


def upsert_refresh_metadata(
    collection_name: str,
    refresh_context: str,
    records_requested: int | None,
    records_inserted: int,
) -> None:
    """
    Guarda metadatos de la ultima actualizacion para una coleccion.
    """
    db = get_db()
    if db is None:
        raise ConnectionError("No se pudo obtener la base de datos.")

    metadata_collection = db[METADATA_COLLECTION]
    metadata_collection.update_one(
        {"collection_name": collection_name},
        {
            "$set": {
                "collection_name": collection_name,
                "last_refresh_at": datetime.now(timezone.utc),
                "refresh_context": refresh_context,
                "records_requested": records_requested,
                "records_inserted": records_inserted,
            }
        },
        upsert=True,
    )


def get_refresh_metadata(collection_name: str) -> dict | None:
    """
    Retorna metadatos de la ultima actualizacion de la coleccion.
    """
    try:
        db = get_db()
        if db is None:
            raise ConnectionError("No se pudo obtener la base de datos.")

        metadata_collection = db[METADATA_COLLECTION]
        document = metadata_collection.find_one({"collection_name": collection_name})
        if not document:
            return None
        if "_id" in document:
            document["_id"] = str(document["_id"])
        return document
    except PyMongoError as e:
        print(f"[mongo_db] Error al leer metadatos: {e}")
        return None
    except Exception as e:
        print(f"[mongo_db] Error inesperado al leer metadatos: {e}")
        return None


def save_data(
    collection_name: str,
    records: list[dict],
    refresh_context: str = "manual-ui",
    records_requested: int | None = None,
    already_cleaned: bool = False,
    insert_batch_size: int = DEFAULT_INSERT_BATCH_SIZE,
) -> int:
    """
    Limpia la coleccion e inserta los registros nuevos.

    Args:
        collection_name: Nombre de la coleccion en MongoDB.
        records: Lista de dicts a insertar.
        refresh_context: Origen de la actualizacion.
        records_requested: Numero solicitado al origen cuando exista.
        already_cleaned: Indica si `records` ya fueron procesados por `clean_records`.
        insert_batch_size: Numero de documentos por lote al insertar en MongoDB.

    Returns:
        Numero de documentos insertados, o 0 si ocurre un error.
    """
    try:
        db = get_db()
        if db is None:
            raise ConnectionError("No se pudo obtener la base de datos.")

        collection = db[collection_name]
        collection.delete_many({})

        if not records:
            return 0

        cleaned_records = records if already_cleaned else clean_records(records)
        insert_batch_size = max(1, int(insert_batch_size))

        # PyMongo agrega `_id` a los documentos insertados; copiamos los registros
        # para no mutar la lista reutilizada por la interfaz.
        documents_to_insert = [dict(record) for record in cleaned_records]

        inserted = 0
        for start in range(0, len(documents_to_insert), insert_batch_size):
            chunk = documents_to_insert[start : start + insert_batch_size]
            result = collection.insert_many(chunk, ordered=False)
            inserted += len(result.inserted_ids)

        print(f"[mongo_db] {inserted} documentos insertados en '{collection_name}'.")
        upsert_refresh_metadata(
            collection_name=collection_name,
            refresh_context=refresh_context,
            records_requested=records_requested if records_requested is not None else len(records),
            records_inserted=inserted,
        )
        return inserted
    except PyMongoError as e:
        print(f"[mongo_db] Error al guardar datos: {e}")
        return 0
    except Exception as e:
        print(f"[mongo_db] Error inesperado al guardar: {e}")
        return 0


def load_data(collection_name: str) -> list[dict]:
    """
    Lee todos los documentos de la coleccion.

    Args:
        collection_name: Nombre de la coleccion en MongoDB.

    Returns:
        Lista de dicts con los documentos (el campo _id convertido a string).
    """
    try:
        db = get_db()
        if db is None:
            raise ConnectionError("No se pudo obtener la base de datos.")

        collection = db[collection_name]
        documents = list(collection.find())

        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        cleaned_documents = clean_records(documents)
        print(f"[mongo_db] {len(cleaned_documents)} documentos leidos de '{collection_name}'.")
        return cleaned_documents
    except PyMongoError as e:
        print(f"[mongo_db] Error al leer datos: {e}")
        return []
    except Exception as e:
        print(f"[mongo_db] Error inesperado al leer: {e}")
        return []
