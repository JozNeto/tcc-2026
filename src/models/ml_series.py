"""Modelo de aprendizado de máquina para série única, via features de defasagem
.

Sem vazamento: cada feature de defasagem usa apenas observações estritamente
anteriores ao alvo — a construção de features aqui nunca
olha para o futuro em relação à linha que está prevendo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor

from src.models.base import COLUNAS_PREVISAO, ModeloSerie
from src.models.baseline import Z_95, proximas_datas


class MLSeriesModel(ModeloSerie):
    """Regressor scikit-learn (padrão: gradient boosting) treinado sobre `n_lags`
    defasagens da própria série. Previsão multi-passo por recursão: cada passo
    previsto realimenta as defasagens do passo seguinte."""

    def __init__(self, n_lags: int = 3, estimator: RegressorMixin | None = None):
        self.n_lags = n_lags
        self.estimator = estimator or GradientBoostingRegressor(random_state=42)

    def _colunas_lag(self) -> list[str]:
        return [f"lag_{i}" for i in range(1, self.n_lags + 1)]

    def _montar_matriz_treino(self, serie: pd.Series) -> pd.DataFrame:
        dados = pd.DataFrame({"y": serie})
        for lag in range(1, self.n_lags + 1):
            dados[f"lag_{lag}"] = serie.shift(lag)
        return dados.dropna()

    def fit(self, serie_treino: pd.Series, exogena_treino: pd.Series | None = None) -> MLSeriesModel:
        serie_limpa = serie_treino.dropna()
        if len(serie_limpa) <= self.n_lags:
            raise ValueError(
                f"MLSeriesModel precisa de mais de n_lags={self.n_lags} observações, recebeu {len(serie_limpa)}"
            )

        dados = self._montar_matriz_treino(serie_limpa)
        X, y = dados[self._colunas_lag()], dados["y"]
        self.estimator.fit(X, y)

        self._residuo_std = float((self.estimator.predict(X) - y).std())
        self._ultima_data = serie_limpa.index[-1]
        self._historico = list(serie_limpa.iloc[-self.n_lags :])
        return self

    def predict(self, horizonte: int, exogena_futura: pd.Series | None = None) -> pd.DataFrame:
        historico = list(self._historico)
        previsoes = []
        for _ in range(horizonte):
            ultimas_defasagens = historico[-self.n_lags :][::-1]  # [lag_1, lag_2, ..., lag_n]
            features = pd.DataFrame([ultimas_defasagens], columns=self._colunas_lag())
            valor_previsto = float(self.estimator.predict(features)[0])
            previsoes.append(valor_previsto)
            historico.append(valor_previsto)

        previsoes_arr = np.array(previsoes)
        passos = np.arange(1, horizonte + 1)
        margem = Z_95 * self._residuo_std * np.sqrt(passos)

        return pd.DataFrame(
            {
                "data_referencia": proximas_datas(self._ultima_data, horizonte),
                "previsao": previsoes_arr,
                "intervalo_inferior": previsoes_arr - margem,
                "intervalo_superior": previsoes_arr + margem,
            }
        )[list(COLUNAS_PREVISAO)]
