"""
Punto de entrada del dashboard de datos abiertos.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from ui_styles import apply_shared_styles, render_hero

load_dotenv()

st.set_page_config(
    page_title="Dashboard COVID Colombia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_shared_styles()

render_hero(
    "Dashboard COVID Colombia",
    "Aplicacion de visualizacion y analisis construida con Streamlit para consumir datos "
    "desde una API publica, limpiarlos y analizarlos sobre MongoDB.",
    badge="Proyecto Integrado",
)
st.markdown("---")

source_url = os.getenv("API_URL", "https://www.datos.gov.co/resource/gt2j-8ykr.json")
collection_name = os.getenv("COLLECTION_NAME", "datos_api")

hero_a, hero_b, hero_c = st.columns(3)
hero_a.metric("Fuente automatizada", "API REST")
hero_b.metric("Persistencia", "MongoDB Atlas")
hero_c.metric("Coleccion activa", collection_name)

st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
st.markdown(
    """
    ## Que resuelve este proyecto

    Este tablero integra todo el flujo de trabajo de visualizacion de datos:

    - extraccion automatizada desde una fuente externa
    - limpieza y enriquecimiento del dataset
    - almacenamiento consultable en MongoDB
    - analisis descriptivo y predictivo en Streamlit
    - visualizaciones interactivas para apoyar decisiones
    """
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")
left, right = st.columns([1.05, 0.95])

with left:
    st.subheader("Ruta recomendada de uso")
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(
        """
        1. **Cargar Datos**: descarga registros desde la API y los almacena en MongoDB.
        2. **Ver Datos**: valida el contenido, aplica filtros y exporta resultados.
        3. **Analisis**: interpreta tendencias, volumen territorial, perfiles demograficos y responde preguntas de negocio con visualizaciones interactivas.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Fortalezas frente a la rubrica")
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown(
        """
        - **Datos**: conexion automatizada a API y MongoDB usando variables de entorno.
        - **Visualizacion**: multiples graficas interactivas con filtros y contexto analitico.
        - **Codigo**: arquitectura modular con separacion clara de responsabilidades.
        - **Despliegue**: proyecto preparado para publicarse con configuracion reproducible.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.subheader("Fuente y alcance")
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.info(
        f"Fuente configurada: {source_url}\n\n"
        "El dataset corresponde a casos de COVID reportados en Colombia y se procesa "
        "para facilitar comparaciones temporales, territoriales y demograficas."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Consejo de sustentacion")
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.success(
        "Empieza mostrando la carga automatizada de datos, luego los filtros de analisis y "
        "termina con las preguntas de negocio y los insights mas relevantes de la pagina de Analisis."
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Fuente de datos: datos.gov.co | Interfaz: Streamlit | Almacenamiento: MongoDB Atlas")
