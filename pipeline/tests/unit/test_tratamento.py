"""Testes unitários de src/features/tratamento.py — dados sintéticos."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from src.features.tratamento import (
    TratamentoError,
    construir_indice_deflator,
    deflacionar,
    imputar_gaps_curtos,
    sinalizar_outliers,
    tratar,
)


def _ipca_sintetico() -> pd.DataFrame:
    # Convenção: o valor na linha do mês X é a variação de X EM RELAÇÃO a X-1 (padrão
    # IPCA "variação mensal"). dez/2024 é dummy (representaria nov->dez, nunca usado
    # aqui, pois não há observação de nov/2024 na série).
    return pd.DataFrame(
        {
            "data_referencia": [dt.date(2024, 12, 1), dt.date(2025, 1, 1), dt.date(2025, 2, 1), dt.date(2025, 3, 1)],
            "valor": [-99.0, 0.5, 10.0, 0.0],  # dez=dummy, jan=dez->jan, fev=jan->fev, mar=fev->mar
        }
    )


def test_construir_indice_deflator_ancora_100_na_data_base():
    indice = construir_indice_deflator(_ipca_sintetico(), data_base=dt.date(2025, 1, 1))
    assert indice.loc[dt.date(2025, 1, 1)] == pytest.approx(100.0)


def test_construir_indice_deflator_acumula_para_frente():
    indice = construir_indice_deflator(_ipca_sintetico(), data_base=dt.date(2025, 1, 1))
    # fev/2025 tem variação de +10% em relação a jan/2025
    assert indice.loc[dt.date(2025, 2, 1)] == pytest.approx(110.0)
    # mar/2025 tem variação de 0% em relação a fev/2025
    assert indice.loc[dt.date(2025, 3, 1)] == pytest.approx(110.0)


def test_construir_indice_deflator_acumula_para_tras():
    indice = construir_indice_deflator(_ipca_sintetico(), data_base=dt.date(2025, 1, 1))
    # dez/2024 -> jan/2025 teve variação de +0,5%; logo dez/2024 = 100 / 1.005
    assert indice.loc[dt.date(2024, 12, 1)] == pytest.approx(100.0 / 1.005)


def test_construir_indice_deflator_levanta_erro_se_vazio():
    with pytest.raises(TratamentoError):
        construir_indice_deflator(pd.DataFrame(columns=["data_referencia", "valor"]), dt.date(2025, 1, 1))


def test_construir_indice_deflator_levanta_erro_se_data_base_fora_da_serie():
    with pytest.raises(TratamentoError):
        construir_indice_deflator(_ipca_sintetico(), data_base=dt.date(2030, 1, 1))


def test_deflacionar_converte_nominal_para_real():
    indice = pd.Series({dt.date(2025, 1, 1): 100.0, dt.date(2025, 2, 1): 110.0})
    nominal = pd.Series({dt.date(2025, 1, 1): 1000.0, dt.date(2025, 2, 1): 1100.0})

    real = deflacionar(nominal, indice)

    assert real.loc[dt.date(2025, 1, 1)] == pytest.approx(1000.0)
    # 1100 nominal em fev, com preços 10% mais altos que jan, vale 1000 em termos reais
    assert real.loc[dt.date(2025, 2, 1)] == pytest.approx(1000.0)


def test_deflacionar_levanta_erro_se_indice_nao_cobre_todas_as_datas():
    indice = pd.Series({dt.date(2025, 1, 1): 100.0})
    nominal = pd.Series({dt.date(2025, 1, 1): 1000.0, dt.date(2025, 2, 1): 1100.0})
    with pytest.raises(TratamentoError):
        deflacionar(nominal, indice)


def test_imputar_gaps_curtos_preenche_gap_de_1_mes():
    datas = pd.date_range("2025-01-01", periods=5, freq="MS").date
    serie = pd.Series([10.0, np.nan, 30.0, 40.0, 50.0], index=datas)

    tratada, mascara = imputar_gaps_curtos(serie, limite_gap=2)

    assert tratada.iloc[1] == pytest.approx(20.0)
    assert mascara.iloc[1]
    assert mascara.sum() == 1


def test_imputar_gaps_curtos_nao_preenche_gap_estrutural_no_inicio():
    """Série que só começa em período recente (gap estrutural) não deve ser
    imputada retroativamente."""
    datas = pd.date_range("2025-01-01", periods=5, freq="MS").date
    serie = pd.Series([np.nan, np.nan, np.nan, 40.0, 50.0], index=datas)

    tratada, mascara = imputar_gaps_curtos(serie, limite_gap=2)

    assert tratada.iloc[:3].isna().all()
    assert not mascara.iloc[:3].any()


def test_imputar_gaps_curtos_nao_preenche_gap_maior_que_o_limite():
    datas = pd.date_range("2025-01-01", periods=6, freq="MS").date
    serie = pd.Series([10.0, np.nan, np.nan, np.nan, np.nan, 60.0], index=datas)

    tratada, mascara = imputar_gaps_curtos(serie, limite_gap=2)

    assert tratada.iloc[1:5].isna().all()
    assert not mascara.any()


def test_sinalizar_outliers_marca_valor_extremo():
    serie = pd.Series([10.0, 11.0, 9.0, 10.5, 9.5, 100.0])
    mascara = sinalizar_outliers(serie, n_desvios=2.0)
    assert mascara.iloc[-1]
    assert not mascara.iloc[:-1].any()


def test_sinalizar_outliers_serie_constante_nao_gera_falso_positivo():
    serie = pd.Series([5.0, 5.0, 5.0, 5.0])
    mascara = sinalizar_outliers(serie, n_desvios=3.0)
    assert not mascara.any()


def test_tratar_deflaciona_apenas_variaveis_monetarias():
    base_long = pd.DataFrame(
        {
            "data_referencia": [dt.date(2025, 1, 1), dt.date(2025, 2, 1)] * 2,
            "unidade": "BR",
            "variavel": ["valor_monetario"] * 2 + ["percentual"] * 2,
            "valor": [1000.0, 1100.0, 50.0, 55.0],
            "fonte": "teste",
            "coletado_em": pd.Timestamp("2026-01-01"),
        }
    )
    ipca = pd.DataFrame(
        {"data_referencia": [dt.date(2025, 1, 1), dt.date(2025, 2, 1)], "valor": [0.0, 10.0]}
    )

    resultado = tratar(
        base_long,
        ipca_variacao_mensal=ipca,
        data_base_deflacao=dt.date(2025, 1, 1),
        variaveis_monetarias={"valor_monetario"},
    )

    assert resultado.loc[dt.date(2025, 2, 1), "valor_monetario"] == pytest.approx(1000.0)
    assert resultado.loc[dt.date(2025, 2, 1), "percentual"] == pytest.approx(55.0)
    assert "valor_monetario_imputado" in resultado.columns
    assert "percentual_outlier" in resultado.columns
