"""Testes unitários de src/features/diagnostico.py — dados sintéticos (spec 02,
critério 3: teste com série sintética conhecida)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.diagnostico import (
    OBSERVACOES_MINIMAS_DECOMPOSICAO,
    SerieCurtaDemaisError,
    avaliar_estacionariedade,
    correlacao_cruzada_defasagens,
    decompor_sazonalidade,
    diagnosticar,
)


def test_avaliar_estacionariedade_diferencia_ruido_branco_de_tendencia():
    rng = np.random.default_rng(0)
    estacionaria = pd.Series(rng.normal(0, 1, size=150))
    tendencia = pd.Series(np.arange(150, dtype=float) + rng.normal(0, 0.1, size=150))

    resultado_estacionaria = avaliar_estacionariedade(estacionaria)
    resultado_tendencia = avaliar_estacionariedade(tendencia)

    assert resultado_estacionaria["adf_rejeita_raiz_unitaria_5pct"] is True
    assert resultado_estacionaria["adf_p_valor"] < resultado_tendencia["adf_p_valor"]


def test_decompor_sazonalidade_levanta_erro_para_serie_curta():
    serie = pd.Series(np.arange(OBSERVACOES_MINIMAS_DECOMPOSICAO - 1, dtype=float))
    with pytest.raises(SerieCurtaDemaisError):
        decompor_sazonalidade(serie, periodo=12)


def test_decompor_sazonalidade_funciona_com_serie_longa_o_suficiente():
    t = np.arange(36)
    serie = pd.Series(10 + 0.1 * t + np.sin(2 * np.pi * t / 12) * 5)
    resultado = decompor_sazonalidade(serie, periodo=12)

    # componente sazonal deve se repetir a cada 12 observações
    assert resultado.seasonal.iloc[0] == pytest.approx(resultado.seasonal.iloc[12], abs=1e-6)


def test_correlacao_cruzada_encontra_defasagem_correta():
    rng = np.random.default_rng(1)
    datas = pd.date_range("2020-01-01", periods=60, freq="MS")
    exogena = pd.Series(rng.normal(size=60), index=datas)
    resposta = exogena.shift(3)  # resposta[t] = exogena[t-3]

    resultado = correlacao_cruzada_defasagens(resposta, exogena, max_defasagem=6)
    melhor_defasagem = resultado.loc[resultado["correlacao"].idxmax(), "defasagem"]

    assert melhor_defasagem == 3
    assert resultado.loc[resultado["defasagem"] == 3, "correlacao"].iloc[0] == pytest.approx(1.0)


def test_correlacao_cruzada_reporta_n_observacoes_pareadas_decrescente():
    datas = pd.date_range("2020-01-01", periods=20, freq="MS")
    serie = pd.Series(np.arange(20, dtype=float), index=datas)

    resultado = correlacao_cruzada_defasagens(serie, serie, max_defasagem=5)

    assert resultado["n_observacoes_pareadas"].is_monotonic_decreasing


def test_diagnosticar_sinaliza_decomposicao_indisponivel_para_serie_curta():
    serie = pd.Series(np.arange(10, dtype=float))
    resultado = diagnosticar(serie)

    assert resultado["decomposicao_disponivel"] is False
    assert resultado["decomposicao"] is None
    assert resultado["aviso_decomposicao"] is not None


def test_diagnosticar_inclui_correlacao_cruzada_quando_exogena_informada():
    t = np.arange(36)
    serie = pd.Series(10 + np.sin(2 * np.pi * t / 12))
    exogena = pd.Series(np.cos(2 * np.pi * t / 12))

    resultado = diagnosticar(serie, serie_exogena=exogena, max_defasagem=3)

    assert "correlacao_cruzada" in resultado
    assert len(resultado["correlacao_cruzada"]) == 4  # defasagens 0..3
