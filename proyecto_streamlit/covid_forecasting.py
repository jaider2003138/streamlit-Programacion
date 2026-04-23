"""
Funciones de pronostico para series temporales mensuales del dashboard COVID.
"""

from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd

from covid_dataframe_utils import DatasetValidationError


logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


def forecast_cases(
    monthly_cases: pd.DataFrame,
    periods: int = 6,
) -> tuple[pd.DataFrame, str]:
    """Genera pronostico futuro para la serie general de casos."""
    return forecast_time_series(monthly_cases, periods=periods, target_name="casos")


def forecast_mortality(
    monthly_deaths: pd.DataFrame,
    periods: int = 6,
) -> tuple[pd.DataFrame, str]:
    """Genera pronostico futuro para la serie mensual de mortalidad."""
    return forecast_time_series(monthly_deaths, periods=periods, target_name="fallecimientos")


def forecast_time_series(
    series_df: pd.DataFrame,
    periods: int = 6,
    target_name: str = "valor",
) -> tuple[pd.DataFrame, str]:
    """
    Pronostica una serie temporal mensual usando Prophet, ARIMA o regresion lineal.

    Returns:
        forecast_df: DataFrame con historico y pronostico
        method_name: Metodo efectivamente usado
    """
    required = {"ds", "y"}
    if not required.issubset(series_df.columns):
        raise DatasetValidationError(
            "La serie temporal debe contener las columnas `ds` y `y`."
        )

    working = series_df.copy().sort_values("ds").reset_index(drop=True)
    working["ds"] = pd.to_datetime(working["ds"], errors="coerce")
    working = working.dropna(subset=["ds", "y"])

    if len(working) < 3:
        raise DatasetValidationError(
            f"No hay suficientes puntos para pronosticar `{target_name}`."
        )

    prophet_forecast = _try_prophet_forecast(working, periods)
    if prophet_forecast is not None:
        return prophet_forecast, "Prophet"

    arima_forecast = _try_arima_forecast(working, periods)
    if arima_forecast is not None:
        return arima_forecast, "ARIMA"

    return _linear_regression_forecast(working, periods), "Regresion temporal"


def _try_prophet_forecast(
    series_df: pd.DataFrame,
    periods: int,
) -> pd.DataFrame | None:
    """Intenta usar Prophet si esta instalado."""
    try:
        from prophet import Prophet
    except Exception:
        return None

    try:
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95,
        )
        model.fit(series_df[["ds", "y"]])
        future = model.make_future_dataframe(periods=periods, freq="MS")
        forecast = model.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result = result.merge(series_df[["ds", "y"]], on="ds", how="left")
        result["tipo"] = np.where(result["y"].notna(), "historico", "pronostico")
        return result
    except Exception:
        return None


def _try_arima_forecast(
    series_df: pd.DataFrame,
    periods: int,
) -> pd.DataFrame | None:
    """Intenta usar ARIMA de statsmodels si esta instalado."""
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except Exception:
        return None

    try:
        y = series_df.set_index("ds")["y"].asfreq("MS")
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Non-stationary starting autoregressive parameters found.*",
                category=UserWarning,
            )
            warnings.filterwarnings(
                "ignore",
                message="Non-invertible starting MA parameters found.*",
                category=UserWarning,
            )
            model = ARIMA(y, order=(1, 1, 1))
            fitted = model.fit()
            prediction = fitted.get_forecast(steps=periods)
        conf = prediction.conf_int()

        future_index = prediction.predicted_mean.index
        future_df = pd.DataFrame(
            {
                "ds": future_index,
                "yhat": prediction.predicted_mean.values,
                "yhat_lower": conf.iloc[:, 0].values,
                "yhat_upper": conf.iloc[:, 1].values,
                "y": np.nan,
                "tipo": "pronostico",
            }
        )

        history_df = pd.DataFrame(
            {
                "ds": series_df["ds"],
                "yhat": series_df["y"],
                "yhat_lower": np.nan,
                "yhat_upper": np.nan,
                "y": series_df["y"],
                "tipo": "historico",
            }
        )

        return pd.concat([history_df, future_df], ignore_index=True)
    except Exception:
        return None


def _linear_regression_forecast(series_df: pd.DataFrame, periods: int) -> pd.DataFrame:
    """
    Fallback simple y robusto cuando no hay librerias de forecasting disponibles.

    Ajusta una tendencia lineal sobre el indice temporal mensual.
    """
    working = series_df.copy().reset_index(drop=True)
    working["t"] = np.arange(len(working), dtype=float)

    slope, intercept = np.polyfit(working["t"], working["y"], deg=1)
    history_pred = intercept + slope * working["t"]
    residual_std = float(np.std(working["y"] - history_pred, ddof=1)) if len(working) > 2 else 0.0

    last_date = working["ds"].max()
    future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    future_t = np.arange(len(working), len(working) + periods, dtype=float)
    future_pred = intercept + slope * future_t

    history_df = pd.DataFrame(
        {
            "ds": working["ds"],
            "yhat": history_pred,
            "yhat_lower": history_pred - 1.96 * residual_std,
            "yhat_upper": history_pred + 1.96 * residual_std,
            "y": working["y"],
            "tipo": "historico",
        }
    )
    future_df = pd.DataFrame(
        {
            "ds": future_dates,
            "yhat": future_pred,
            "yhat_lower": future_pred - 1.96 * residual_std,
            "yhat_upper": future_pred + 1.96 * residual_std,
            "y": np.nan,
            "tipo": "pronostico",
        }
    )

    return pd.concat([history_df, future_df], ignore_index=True)
