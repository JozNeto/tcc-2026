from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.base import validar_saida_previsao
from src.models.econometricos import SARIMAXModel


def _serie_ar(n: int = 60, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    valores = [0.0]
    for _ in range(n - 1):
        valores.append(0.6 * valores[-1] + rng.normal(0, 1))
    datas = pd.date_range("2020-01-01", periods=n, freq="MS").date
    return pd.Series(valores, index=datas)


def test_sarimax_sem_exogena_produz_saida_valida():
    serie = _serie_ar()
    modelo = SARIMAXModel(order=(1, 0, 0)).fit(serie)

    previsao = modelo.predict(horizonte=6)

    validar_saida_previsao(previsao)
    assert len(previsao) == 6


def test_sarimax_com_exogena_exige_exogena_futura_no_predict():
    serie = _serie_ar()
    exogena = _serie_ar(seed=1)
    modelo = SARIMAXModel(order=(1, 0, 0)).fit(serie, exogena_treino=exogena)

    with pytest.raises(ValueError, match="exogena_futura"):
        modelo.predict(horizonte=3)


def test_sarimax_com_exogena_funciona_quando_exogena_futura_informada():
    serie = _serie_ar()
    exogena = _serie_ar(seed=1)
    modelo = SARIMAXModel(order=(1, 0, 0)).fit(serie, exogena_treino=exogena)

    datas_futuras = pd.date_range("2025-01-01", periods=3, freq="MS").date
    exogena_futura = pd.Series([0.1, 0.2, 0.3], index=datas_futuras)

    previsao = modelo.predict(horizonte=3, exogena_futura=exogena_futura)

    validar_saida_previsao(previsao)
    assert len(previsao) == 3
