"""
Estilos visuales compartidos para las paginas del dashboard.
"""

from __future__ import annotations

import streamlit as st


def apply_shared_styles() -> None:
    """Inyecta estilos visuales reutilizables para toda la app."""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.14), transparent 28%),
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 24%),
                linear-gradient(180deg, #f6fbfb 0%, #eef5f4 52%, #f7fafb 100%);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(10px);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(233, 243, 241, 0.98) 0%, rgba(245, 250, 249, 0.98) 100%);
            border-right: 1px solid rgba(15, 118, 110, 0.10);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero-panel {
            padding: 1.4rem 1.5rem;
            border-radius: 24px;
            background:
                linear-gradient(135deg, rgba(11, 36, 61, 0.96), rgba(15, 118, 110, 0.88));
            color: #f8fcfc;
            box-shadow: 0 24px 50px rgba(15, 23, 42, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.10);
            margin-bottom: 1rem;
        }

        .hero-panel h1,
        .hero-panel h2,
        .hero-panel h3,
        .hero-panel p,
        .hero-panel li {
            color: #f8fcfc !important;
        }

        .glass-panel {
            padding: 1rem 1.15rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(15, 118, 110, 0.12);
            box-shadow: 0 16px 32px rgba(15, 23, 42, 0.07);
        }

        .question-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.35rem;
        }

        .question-card {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(243,248,247,0.95));
            border: 1px solid rgba(15, 118, 110, 0.10);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            font-size: 0.96rem;
            line-height: 1.45;
        }

        .kpi-note {
            padding: 1rem 1.1rem;
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(235, 245, 244, 0.95), rgba(255, 255, 255, 0.95));
            border: 1px solid rgba(15, 118, 110, 0.10);
            margin-bottom: 0.75rem;
        }

        .section-chip {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(15, 118, 110, 0.12);
            color: #0f4f4a;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(15, 118, 110, 0.12);
            padding: 0.95rem 1rem;
            border-radius: 18px;
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
        }

        div[data-testid="stDataFrame"],
        .stPlotlyChart,
        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.74);
            border-radius: 18px;
        }

        div[role="radiogroup"] {
            gap: 0.5rem;
        }

        div[role="radiogroup"] label {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(15, 118, 110, 0.12);
            border-radius: 999px;
            padding: 0.3rem 0.8rem;
        }

        @media (max-width: 900px) {
            .question-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, description: str, badge: str | None = None) -> None:
    """Renderiza una cabecera visual compartida."""
    badge_html = f'<div class="section-chip">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="hero-panel">
            {badge_html}
            <h1 style="margin:0 0 0.35rem 0;">{title}</h1>
            <p style="margin:0; font-size:1rem; max-width:860px;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_question_grid(questions: list[str]) -> None:
    """Muestra preguntas de negocio en formato de tarjetas."""
    cards = "".join(
        f'<div class="question-card">{idx + 1}. {question}</div>'
        for idx, question in enumerate(questions)
    )
    st.markdown(f'<div class="question-grid">{cards}</div>', unsafe_allow_html=True)
