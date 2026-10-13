"""Testes unitários de src/features/quebras_estruturais.py — série sintética com
quebra em posição conhecida."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from src.features.quebras_estruturais import (
    confrontar_com_calendario_regulatorio,
    detectar_quebras,
)

TOLERANCIA_MESES = 1


def _serie_com_quebra_conhecida(posicao_quebra: int = 30, tamanho: int = 60) -> tuple[pd.Series, dt.date]:
    datas = list(pd.date_range("2021-01-01", periods=tamanho, freq="MS").date)
    valores = [10.0] * posicao_quebra + [80.0] * (tamanho - posicao_quebra)
    serie = pd.Series(valores, index=datas)
    data_quebra_esperada = datas[posicao_quebra]
    return serie, data_quebra_esperada


def test_detectar_quebras_recupera_posicao_conhecida_com_n_quebras_fixo():
    serie, data_esperada = _serie_com_quebra_conhecida()

    quebras = detectar_quebras(serie, n_quebras=1)

    assert len(quebras) == 1
    diferenca_dias = abs((quebras[0] - data_esperada).days)
    assert diferenca_dias <= 31 * TOLERANCIA_MESES


def test_detectar_quebras_ignora_nan():
    serie, data_esperada = _serie_com_quebra_conhecida()
    serie_com_gap = serie.copy()
    serie_com_gap.iloc[5] = float("nan")

    quebras = detectar_quebras(serie_com_gap, n_quebras=1)

    assert len(quebras) == 1
    assert abs((quebras[0] - data_esperada).days) <= 31 * TOLERANCIA_MESES


def test_detectar_quebras_serie_sem_quebra_com_penalidade_alta_nao_gera_falso_positivo():
    datas = list(pd.date_range("2021-01-01", periods=36, freq="MS").date)
    serie_constante = pd.Series([10.0] * 36, index=datas)

    quebras = detectar_quebras(serie_constante, penalidade=50.0)

    assert quebras == []


def test_confrontar_com_calendario_identifica_coincidencia_dentro_da_tolerancia():
    calendario = {"marco_teste": dt.date(2025, 6, 1)}
    quebras = [dt.date(2025, 6, 10)]

    resultado = confrontar_com_calendario_regulatorio(quebras, calendario, tolerancia_dias=45)

    linha = resultado.iloc[0]
    assert linha["coincide_dentro_da_tolerancia"]
    assert linha["distancia_dias"] == 9


def test_confrontar_com_calendario_marca_nao_coincidencia_fora_da_tolerancia():
    calendario = {"marco_teste": dt.date(2025, 6, 1)}
    quebras = [dt.date(2024, 1, 1)]

    resultado = confrontar_com_calendario_regulatorio(quebras, calendario, tolerancia_dias=45)

    assert not resultado.iloc[0]["coincide_dentro_da_tolerancia"]


def test_confrontar_com_calendario_lida_com_lista_de_quebras_vazia():
    resultado = confrontar_com_calendario_regulatorio([], {"marco_teste": dt.date(2025, 6, 1)})

    assert resultado.iloc[0]["quebra_mais_proxima"] is None
    assert not resultado.iloc[0]["coincide_dentro_da_tolerancia"]


def test_confrontar_com_calendario_usa_calendario_padrao_de_2025():
    resultado = confrontar_com_calendario_regulatorio([dt.date(2025, 1, 15)])
    assert set(resultado["marco"]) == {
        "regulamentacao_mercado",
        "restricao_beneficiarios",
        "suspensao_parcial_judicial",
    }
