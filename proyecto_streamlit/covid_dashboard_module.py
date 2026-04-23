"""
Fachada del dashboard COVID.

Mantiene una API publica estable mientras delega responsabilidades en:
- covid_dataframe_utils: carga, validacion y preparacion del dataset
- covid_forecasting: pronosticos temporales
- covid_visualization_utils: construccion de figuras
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from covid_dataframe_utils import (
    DatasetValidationError,
    load_clean_dataset,
    prepare_clean_dataframe,
    prepare_monthly_series,
    prepare_mortality_series,
)
from covid_forecasting import (
    forecast_cases,
    forecast_mortality,
    forecast_time_series,
)
from covid_visualization_utils import (
    build_combined_dashboard,
    build_info_figure,
    generate_additional_plots,
    generate_additional_plots_with_options,
    plot_age_group_stacked_area,
    plot_cases_by_city,
    plot_cases_by_department,
    plot_gender_distribution_deceased,
    plot_general_cases_forecast,
    plot_health_state_trends,
    plot_mortality_forecast,
    plot_top_departments_time_series,
    select_default_health_states,
)


def generate_dashboard_from_file(
    path: str | Path,
    forecast_periods: int = 6,
) -> dict[str, Any]:
    """
    Funcion principal que carga el dataset y construye todas las figuras.

    Returns:
        Diccionario con el dataframe y las figuras generadas.
    """
    df = load_clean_dataset(path)
    return generate_dashboard_from_dataframe(df, forecast_periods=forecast_periods)


def generate_dashboard_from_dataframe(
    df: pd.DataFrame,
    forecast_periods: int = 6,
    selected_states: list[str] | None = None,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    """
    Construye todas las figuras del dashboard a partir de un DataFrame.

    Args:
        df: DataFrame limpio.
        forecast_periods: Meses futuros a pronosticar.
        selected_states: Estados opcionales para la grafica comparativa.
        start_date: Fecha inicial opcional para la grafica de estados.
        end_date: Fecha final opcional para la grafica de estados.

    Returns:
        Diccionario con el dataframe preparado y las figuras generadas.
    """
    prepared_df = prepare_clean_dataframe(df)

    monthly_cases = prepare_monthly_series(
        prepared_df,
        date_column="mes_reporte",
        count_column_name="casos",
    )
    cases_forecast, cases_method = forecast_cases(monthly_cases, periods=forecast_periods)

    monthly_deaths = prepare_mortality_series(prepared_df)
    mortality_forecast, mortality_method = forecast_mortality(
        monthly_deaths,
        periods=forecast_periods,
    )

    cases_fig = plot_general_cases_forecast(monthly_cases, cases_forecast, cases_method)
    top_departments_fig = plot_top_departments_time_series(prepared_df, top_n=5)
    mortality_fig = plot_mortality_forecast(monthly_deaths, mortality_forecast, mortality_method)
    age_fig = plot_age_group_stacked_area(prepared_df)
    additional_figs = generate_additional_plots_with_options(
        prepared_df,
        selected_states=selected_states,
        start_date=start_date,
        end_date=end_date,
    )
    dashboard_fig = build_combined_dashboard(
        cases_fig,
        top_departments_fig,
        mortality_fig,
        age_fig,
    )

    return {
        "dataframe": prepared_df,
        "monthly_cases": monthly_cases,
        "monthly_deaths": monthly_deaths,
        "cases_forecast": cases_forecast,
        "mortality_forecast": mortality_forecast,
        "cases_method": cases_method,
        "mortality_method": mortality_method,
        "last_updated": pd.Timestamp.utcnow(),
        "fig_cases": cases_fig,
        "fig_top_departments": top_departments_fig,
        "fig_mortality": mortality_fig,
        "fig_age": age_fig,
        "fig_dashboard": dashboard_fig,
        **additional_figs,
    }


def save_dashboard_html(
    dashboard_fig,
    output_path: str | Path,
) -> None:
    """Guarda el dashboard final como HTML."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dashboard_fig.write_html(output)


if __name__ == "__main__":
    example_path = Path("data_exports/covid_api_limpio_2000.csv")
    if example_path.exists():
        result = generate_dashboard_from_file(example_path, forecast_periods=6)
        save_dashboard_html(
            result["fig_dashboard"],
            Path("data_exports/dashboard_covid.html"),
        )
        df = load_clean_dataset(example_path)
        plot_cases_by_department(df)
        plot_cases_by_city(df)
        plot_health_state_trends(df, ["Leve", "Grave", "Fallecido"])
        plot_gender_distribution_deceased(df)
        print("Dashboard generado correctamente.")
        print(f"Metodo de pronostico de casos: {result['cases_method']}")
        print(f"Metodo de pronostico de mortalidad: {result['mortality_method']}")
    else:
        print(
            "Ejemplo no ejecutado: no se encontro el archivo "
            f"{example_path.resolve()}"
        )
