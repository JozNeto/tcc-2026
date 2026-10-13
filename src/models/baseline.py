"""Modelos baseline: naive e seasonal naive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.base import COLUNAS_PREVISAO, ModeloSerie

Z_95 = 1.959963985  # quantil normal padrão para intervalo de 95%


def proximas_datas(ultima_data, horizonte: int, freq: str = "MS") -> list:
    """Gera `horizonte` datas mensais subsequentes a `ultima_data` (exclusive)."""
    return list(pd.date_range(start=ultima_data, periods=horizonte + 1, freq=freq)[1:].date)


class NaiveModel(ModeloSerie):
    """Repete o último valor observado. Intervalo de predição cresce com
    `sqrt(passo)` a partir do desvio-padrão das primeiras diferenças da série de
    treino — a forma clássica de intervalo do naive (Hyndman & Athanasopoulos)."""

    def fit(self, serie_treino: pd.Series, exogena_treino: pd.Series | None = None) -> NaiveModel:
        serie_limpa = serie_treino.dropna()
        if len(serie_limpa) < 2:
            raise ValueError("NaiveModel precisa de ao menos 2 observações para estimar o desvio-padrão dos resíduos")
        self._ultimo_valor = float(serie_limpa.iloc[-1])
        self._ultima_data = serie_limpa.index[-1]
        self._desvio_residuos = float(serie_limpa.diff().dropna().std())
        return self

    def predict(self, horizonte: int, exogena_futura: pd.Series | None = None) -> pd.DataFrame:
        datas = proximas_datas(self._ultima_data, horizonte)
        passos = np.arange(1, horizonte + 1)
        margem = Z_95 * self._desvio_residuos * np.sqrt(passos)
        return pd.DataFrame(
            {
                "data_referencia": datas,
                "previsao": self._ultimo_valor,
                "intervalo_inferior": self._ultimo_valor - margem,
                "intervalo_superior": self._ultimo_valor + margem,
            }
        )[list(COLUNAS_PREVISAO)]


class SeasonalNaiveModel(ModeloSerie):
    """Repete o valor do mesmo período do ciclo sazonal anterior (padrão: mês
    correspondente 12 meses atrás). Intervalo de predição a partir do desvio-padrão
    das diferenças sazonais (`serie - serie.shift(periodo)`)."""

    def __init__(self, periodo: int = 12):
        self.periodo = periodo

    def fit(self, serie_treino: pd.Series, exogena_treino: pd.Series | None = None) -> SeasonalNaiveModel:
        serie_limpa = serie_treino.dropna()
        if len(serie_limpa) < self.periodo + 1:
            raise ValueError(
                f"SeasonalNaiveModel precisa de mais de {self.periodo} observações "
                f"(1 ciclo sazonal completo), recebeu {len(serie_limpa)}"
            )
        self._ultimo_ciclo = serie_limpa.iloc[-self.periodo :].to_numpy()
        self._ultima_data = serie_limpa.index[-1]
        self._desvio_residuos = float((serie_limpa - serie_limpa.shift(self.periodo)).dropna().std())
        return self

    def predict(self, horizonte: int, exogena_futura: pd.Series | None = None) -> pd.DataFrame:
        datas = proximas_datas(self._ultima_data, horizonte)
        previsoes = [self._ultimo_ciclo[(h - 1) % self.periodo] for h in range(1, horizonte + 1)]
        # margem cresce a cada ciclo sazonal completo repetido, não a cada passo —
        # convenção usual para seasonal naive (Hyndman & Athanasopoulos, cap. 3.4)
        multiplicadores_ciclo = np.array([((h - 1) // self.periodo) + 1 for h in range(1, horizonte + 1)])
        margem = Z_95 * self._desvio_residuos * np.sqrt(multiplicadores_ciclo)
        previsoes = np.array(previsoes, dtype=float)
        return pd.DataFrame(
            {
                "data_referencia": datas,
                "previsao": previsoes,
                "intervalo_inferior": previsoes - margem,
                "intervalo_superior": previsoes + margem,
            }
        )[list(COLUNAS_PREVISAO)]
