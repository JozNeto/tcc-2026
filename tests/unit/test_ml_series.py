from __future__ import annotations

import pandas as pd
import pytest

from src.models.base import validar_saida_previsao
from src.models.ml_series import MLSeriesModel


def _serie_periodica(n_ciclos: int = 8, periodo: int = 3) -> pd.Series:
    valores = ([1.0, 2.0, 3.0] * n_ciclos)[: n_ciclos * periodo]
    datas = pd.date_range("2018-01-01", periods=len(valores), freq="MS").date
    return pd.Series(valores, index=datas)


def test_ml_series_produz_saida_valida():
    serie = _serie_periodica()
    modelo = MLSeriesModel(n_lags=3).fit(serie)

    previsao = modelo.predict(horizonte=6)

    validar_saida_previsao(previsao)
    assert len(previsao) == 6


def test_ml_series_levanta_erro_com_poucas_observacoes():
    serie = pd.Series([1.0, 2.0], index=pd.date_range("2020-01-01", periods=2, freq="MS").date)
    with pytest.raises(ValueError):
        MLSeriesModel(n_lags=3).fit(serie)


def test_ml_series_aprende_padrao_periodico_sem_ruido():
    """Com um padrão perfeitamente periódico e repetido muitas vezes, um regressor
    de árvores deve conseguir memorizar a transição lag->próximo valor."""
    serie = _serie_periodica(n_ciclos=20, periodo=3)
    modelo = MLSeriesModel(n_lags=3).fit(serie)

    previsao = modelo.predict(horizonte=3)

    # a série termina em [..., 1, 2, 3]; o próximo ciclo esperado é [1, 2, 3]
    assert previsao["previsao"].round().tolist() == [1.0, 2.0, 3.0]


def test_ml_series_intervalo_cresce_com_horizonte():
    serie = _serie_periodica(n_ciclos=20, periodo=3)
    modelo = MLSeriesModel(n_lags=3).fit(serie)

    previsao = modelo.predict(horizonte=5)
    larguras = previsao["intervalo_superior"] - previsao["intervalo_inferior"]

    assert larguras.is_monotonic_increasing
