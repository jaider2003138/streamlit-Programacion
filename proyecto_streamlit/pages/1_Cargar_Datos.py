"""
Pagina para descargar datos desde la API publica y guardarlos en MongoDB.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api_service import fetch_data, fetch_total_count
from data_cleaning import clean_records
from mongo_db import get_refresh_metadata, save_data
from ui_styles import apply_shared_styles, render_hero

load_dotenv()

st.set_page_config(page_title="Cargar Datos", page_icon="⬇️", layout="wide")
apply_shared_styles()

render_hero(
    "Cargar Datos desde la API",
    "Descarga registros desde datos.gov.co, aplica limpieza automatizada y los almacena en MongoDB Atlas.",
    badge="Extraccion",
)
st.markdown("---")

api_url = os.getenv("API_URL", "https://www.datos.gov.co/resource/gt2j-8ykr.json")
collection_name = os.getenv("COLLECTION_NAME", "datos_api")
refresh_metadata = get_refresh_metadata(collection_name)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Fuente", "API REST")
col_b.metric("Destino", "MongoDB Atlas")
col_c.metric("Coleccion", collection_name)

with st.expander("Como aporta esta pagina a la rubrica", expanded=False):
    st.markdown(
        """
        - Automatiza la extraccion desde una fuente externa.
        - Usa variables de entorno para no exponer credenciales en el codigo.
        - Permite repetir la carga cuando se necesite actualizar la informacion.
        - Incluye un script `auto_update.py` para programar actualizaciones sin intervencion manual.
        """
    )

if refresh_metadata:
    refresh_at = pd.to_datetime(refresh_metadata.get("last_refresh_at"), errors="coerce")
    refresh_label = refresh_at.strftime("%Y-%m-%d %H:%M UTC") if not pd.isna(refresh_at) else "Sin dato"
    refresh_context = refresh_metadata.get("refresh_context", "Sin dato")
    refresh_inserted = refresh_metadata.get("records_inserted", "Sin dato")
    st.caption(
        f"Ultima actualizacion registrada: {refresh_label} | "
        f"Origen: {refresh_context} | Documentos insertados: {refresh_inserted}"
    )

total_registros = fetch_total_count(api_url)

status_left, status_right = st.columns([1.25, 0.75])
with status_left:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    if total_registros is not None:
        st.info(f"El recurso original reporta aproximadamente **{total_registros:,}** registros.")
    else:
        st.info(
            "No fue posible consultar el total del recurso, pero aun puedes cargar una muestra "
            "o intentar la descarga completa."
        )
    st.markdown("</div>", unsafe_allow_html=True)

with status_right:
    st.markdown('<div class="kpi-note">', unsafe_allow_html=True)
    st.markdown(
        f"""
        **Fuente configurada**  
        `{api_url}`
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

cargar_todo = st.checkbox(
    "Usar el 100% de los datos del endpoint",
    value=False,
    help="Si esta activo, la app descarga todos los registros disponibles mediante paginacion.",
)

cantidad = None
if not cargar_todo:
    max_slider = 60_000
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    cantidad = st.slider(
        "Cantidad de registros a cargar",
        min_value=0,
        max_value=max_slider,
        value=0,
        step=100,
        help="Numero de registros a consultar en esta corrida.",
    )
    st.caption(f"Se cargara una muestra de **{cantidad:,}** registros desde `{api_url}`.")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.warning(
        "La descarga completa puede tardar varios minutos y consumir mas memoria, "
        "especialmente en entornos de despliegue."
    )
    st.caption(f"Se intentara descargar el conjunto completo desde `{api_url}`.")
    st.markdown("</div>", unsafe_allow_html=True)

if st.button("Cargar datos desde API", type="primary"):
    if not cargar_todo and cantidad == 0:
        st.warning("Selecciona una cantidad mayor a 0 para iniciar la carga.")
        st.stop()

    with st.spinner("Consultando la API..."):
        try:
            registros = fetch_data(api_url, limit=cantidad if not cargar_todo else None)

            if not registros:
                st.error(
                    "No se obtuvieron datos de la API. Verifica la URL configurada o la conexion a internet."
                )
            else:
                with st.spinner("Limpiando y estandarizando datos..."):
                    cleaned_records = clean_records(registros)
                with st.spinner("Guardando en MongoDB..."):
                    insertados = save_data(
                        collection_name,
                        cleaned_records,
                        records_requested=len(registros),
                        already_cleaned=True,
                    )

                if insertados > 0:
                    st.cache_data.clear()
                    st.session_state["last_data_refresh"] = datetime.utcnow().isoformat()
                    st.success(
                        f"Se insertaron **{insertados:,}** registros en MongoDB despues de aplicar limpieza."
                    )

                    info_a, info_b, info_c = st.columns(3)
                    info_a.metric("Registros descargados", f"{len(registros):,}")
                    info_b.metric("Registros limpios", f"{len(cleaned_records):,}")
                    info_c.metric(
                        "Ultima actualizacion",
                        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    )

                    df_preview = pd.DataFrame(cleaned_records[:5])
                    st.markdown("")
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.subheader("Vista previa limpia")
                    st.dataframe(df_preview, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(
                        "Los datos se obtuvieron, pero no pudieron guardarse en MongoDB. "
                        "Revisa las credenciales y la conectividad."
                    )

        except Exception as e:
            st.error(f"Error inesperado durante la carga: {e}")

with st.expander("Automatizacion sin intervencion manual", expanded=False):
    st.markdown(
        """
        Puedes programar una actualizacion automatica con el script:

        ```bash
        python proyecto_streamlit/auto_update.py --full
        ```

        O limitar la carga automatica:

        ```bash
        python proyecto_streamlit/auto_update.py --limit 5000
        ```

        Esto permite usar Task Scheduler en Windows o cron en Linux para cumplir un flujo de actualizacion periodica.
        """
    )
