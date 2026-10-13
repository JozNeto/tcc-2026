"""Modelo econométrico com variáveis exógenas — SARIMAX.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.models.base import COLUNAS_PREVISAO, ModeloSerie
from src.models.baseline import proximas_datas


class SARIMAXModel(ModeloSerie):
    """Wrapper de `statsmodels.tsa.statespace.sarimax.SARIMAX` na interface comum do
    projeto. A escolha de `order`/`seasonal_order` é responsabilidade de quem chama
    (calibrar por série e documentar se sair do padrão) — este módulo não
    faz busca automática de hiperparâmetros."""

    def __init__(self, order: tuple = (1, 1, 1), seasonal_order: tuple = (0, 0, 0, 0)):
        self.order = order
        self.seasonal_order = seasonal_order

    def fit(self, serie_treino: pd.Series, exogena_treino: pd.Series | None = None) -> SARIMAXModel:
        serie_limpa = serie_treino.dropna()
        exog = exogena_treino.reindex(serie_limpa.index).to_numpy() if exogena_treino is not None else None

        self._ultima_data = serie_limpa.index[-1]
        self._usa_exogena = exogena_treino is not None
        modelo = SARIMAX(
            serie_limpa.to_numpy(),
            exog=exog,
            order=self.order,
            seasonal_order=self.seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        self._resultado = modelo.fit(disp=False)
        return self

    def predict(self, horizonte: int, exogena_futura: pd.Series | None = None) -> pd.DataFrame:
        if self._usa_exogena and exogena_futura is None:
            raise ValueError("modelo foi treinado com variável exógena — exogena_futura é obrigatória em predict()")

        exog = exogena_futura.to_numpy().reshape(-1, 1) if exogena_futura is not None else None
        previsao = self._resultado.get_forecast(steps=horizonte, exog=exog)
        intervalo = previsao.conf_int(alpha=0.05)

        return pd.DataFrame(
            {
                "data_referencia": proximas_datas(self._ultima_data, horizonte),
                "previsao": np.asarray(previsao.predicted_mean),
                "intervalo_inferior": np.asarray(intervalo)[:, 0],
                "intervalo_superior": np.asarray(intervalo)[:, 1],
            }
        )[list(COLUNAS_PREVISAO)]
