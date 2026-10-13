from __future__ import annotations

import pandas as pd
import pytest

from src.models.base import validar_saida_previsao
from src.models.baseline import NaiveModel, SeasonalNaiveModel, proximas_datas


def _serie(valores: list[float], inicio: str = "2020-01-01") -> pd.Series:
    datas = pd.date_range(inicio, periods=len(valores), freq="MS").date
    return pd.Series(valores, index=datas)


def test_proximas_datas_gera_meses_subsequentes():
    datas = proximas_datas(pd.Timestamp("2025-12-01"), horizonte=3)
    assert datas == [pd.Timestamp("2026-01-01").date(), pd.Timestamp("2026-02-01").date(), pd.Timestamp("2026-03-01").date()]


def test_naive_model_repete_ultimo_valor():
    serie = _serie([10.0, 12.0, 11.0, 13.0])
    modelo = NaiveModel().fit(serie)

    previsao = modelo.predict(horizonte=3)

    validar_saida_previsao(previsao)
    assert (previsao["previsao"] == 13.0).all()
    assert len(previsao) == 3


def test_naive_model_intervalo_cresce_com_horizonte():
    serie = _serie([10.0, 12.0, 9.0, 14.0, 8.0, 15.0])
    modelo = NaiveModel().fit(serie)

    previsao = modelo.predict(horizonte=4)
    larguras = previsao["intervalo_superior"] - previsao["intervalo_inferior"]

    assert larguras.is_monotonic_increasing
    assert larguras.iloc[0] > 0


def test_naive_model_levanta_erro_com_menos_de_2_observacoes():
    with pytest.raises(ValueError):
        NaiveModel().fit(_serie([10.0]))


def test_seasonal_naive_repete_ciclo_anterior():
    # 24 meses: ciclo 1 = 1..12, ciclo 2 = 1..12 (idêntico, sem ruído)
    valores = list(range(1, 13)) * 2
    serie = _serie([float(v) for v in valores])
    modelo = SeasonalNaiveModel(periodo=12).fit(serie)

    previsao = modelo.predict(horizonte=12)

    validar_saida_previsao(previsao)
    assert previsao["previsao"].tolist() == [float(v) for v in range(1, 13)]


def test_seasonal_naive_repete_o_ciclo_de_novo_apos_12_passos():
    valores = list(range(1, 13)) * 2
    serie = _serie([float(v) for v in valores])
    modelo = SeasonalNaiveModel(periodo=12).fit(serie)

    previsao = modelo.predict(horizonte=24)

    assert previsao["previsao"].iloc[12:].tolist() == previsao["previsao"].iloc[:12].tolist()


def test_seasonal_naive_levanta_erro_com_menos_de_1_ciclo():
    serie = _serie([1.0] * 10)
    with pytest.raises(ValueError):
        SeasonalNaiveModel(periodo=12).fit(serie)


def test_validar_saida_previsao_rejeita_intervalo_invertido():
    df = pd.DataFrame(
        {
            "data_referencia": [pd.Timestamp("2026-01-01").date()],
            "previsao": [10.0],
            "intervalo_inferior": [20.0],
            "intervalo_superior": [5.0],
        }
    )
    with pytest.raises(ValueError):
        validar_saida_previsao(df)
