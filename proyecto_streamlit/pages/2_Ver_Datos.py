"""
Pagina para explorar, filtrar y exportar los datos almacenados en MongoDB.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dashboard_page_utils import dataframe_to_csv_bytes, load_collection_dataframe
from ui_styles import apply_shared_styles, render_hero

load_dotenv()

st.set_page_config(page_title="Ver Datos", page_icon="🔍", layout="wide")
apply_shared_styles()

render_hero(
    "Ver Datos",
    "Explora, busca, filtra y exporta los registros almacenados en MongoDB desde una vista mas clara y util para validacion.",
    badge="Exploracion",
)
st.markdown("---")

collection_name = os.getenv("COLLECTION_NAME", "datos_api")
df = load_collection_dataframe(collection_name)

if df.empty:
    st.warning("Primero carga datos desde la pagina 1.")
    st.stop()

top_a, top_b, top_c = st.columns(3)
top_a.metric("Total de registros", f"{len(df):,}")
top_b.metric("Columnas", f"{len(df.columns):,}")
top_c.metric("Coleccion", collection_name)

control_left, control_right = st.columns([0.95, 1.05])

with control_left:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    busqueda = st.text_input(
        "Buscar en todas las columnas",
        placeholder="Escribe un termino para filtrar...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

if busqueda:
    mask = df.apply(
        lambda col: col.astype(str).str.contains(busqueda, case=False, na=False)
    ).any(axis=1)
    df_filtrado = df[mask]
else:
    df_filtrado = df.copy()

columnas_disponibles = df_filtrado.columns.tolist()

with control_right:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    columnas_seleccionadas = st.multiselect(
        "Columnas a mostrar",
        options=columnas_disponibles,
        default=columnas_disponibles[: min(12, len(columnas_disponibles))],
    )
    st.markdown("</div>", unsafe_allow_html=True)

df_vista = df_filtrado[columnas_seleccionadas] if columnas_seleccionadas else df_filtrado

summary_left, summary_right = st.columns([1.25, 0.75])
with summary_left:
    st.markdown('<div class="kpi-note">', unsafe_allow_html=True)
    st.markdown(f"Mostrando **{len(df_vista):,}** registros despues del filtro textual.")
    st.markdown("</div>", unsafe_allow_html=True)
with summary_right:
    st.download_button(
        label="Descargar vista actual como CSV",
        data=dataframe_to_csv_bytes(df_vista),
        file_name="datos_exportados.csv",
        mime="text/csv",
    )

st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
st.dataframe(df_vista, use_container_width=True, height=540)
st.markdown("</div>", unsafe_allow_html=True)
