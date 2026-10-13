"""Testes unitários de src/features/indicador_territorial.py — dados sintéticos.
Verifica também as restrições metodológicas (sem projeção no Recorte 1,
sem modelagem no Recorte 2) indiretamente: nenhuma função aqui aceita horizonte de
projeção nem ajusta modelo — a API em si não oferece como violar a restrição.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from src.features.indicador_territorial import (
    IndicadorTerritorialError,
    caracterizar_municipios,
    construir_indicador_composto,
    identificar_uf_maior_exposicao,
    normalizar_min_max,
)


def test_normalizar_min_max_mapeia_extremos_para_0_e_1():
    serie = pd.Series({"SP": 100.0, "RJ": 50.0, "AC": 0.0})
    normalizado = normalizar_min_max(serie)
    assert normalizado["SP"] == pytest.approx(1.0)
    assert normalizado["AC"] == pytest.approx(0.0)
    assert normalizado["RJ"] == pytest.approx(0.5)


def test_normalizar_min_max_serie_constante_retorna_neutro():
    serie = pd.Series({"SP": 10.0, "RJ": 10.0})
    normalizado = normalizar_min_max(serie)
    assert (normalizado == 0.5).all()


def test_construir_indicador_composto_pesos_iguais_por_padrao():
    componentes = {
        "google_trends": pd.Series({"SP": 100.0, "RJ": 0.0}),
        "bolsa_familia_per_capita": pd.Series({"SP": 0.0, "RJ": 100.0}),
    }
    resultado = construir_indicador_composto(componentes)

    # SP: trends=1.0, bolsa=0.0 -> média 0.5 | RJ: trends=0.0, bolsa=1.0 -> média 0.5
    assert resultado.loc["SP", "indicador_composto"] == pytest.approx(0.5)
    assert resultado.loc["RJ", "indicador_composto"] == pytest.approx(0.5)
    assert resultado["exploratorio"].all()


def test_construir_indicador_composto_respeita_pesos_informados():
    componentes = {
        "a": pd.Series({"SP": 100.0, "RJ": 0.0}),
        "b": pd.Series({"SP": 0.0, "RJ": 100.0}),
    }
    resultado = construir_indicador_composto(componentes, pesos={"a": 3.0, "b": 1.0})

    # SP: (1.0*3 + 0.0*1) / 4 = 0.75
    assert resultado.loc["SP", "indicador_composto"] == pytest.approx(0.75)


def test_construir_indicador_composto_levanta_erro_se_pesos_nao_cobrem_componentes():
    componentes = {"a": pd.Series({"SP": 1.0}), "b": pd.Series({"SP": 2.0})}
    with pytest.raises(IndicadorTerritorialError):
        construir_indicador_composto(componentes, pesos={"a": 1.0})


def test_construir_indicador_composto_levanta_erro_se_vazio():
    with pytest.raises(IndicadorTerritorialError):
        construir_indicador_composto({})


def test_identificar_uf_maior_exposicao():
    indicador = pd.DataFrame({"indicador_composto": [0.2, 0.9, 0.5]}, index=["AC", "SP", "RJ"])
    assert identificar_uf_maior_exposicao(indicador) == "SP"


def test_caracterizar_municipios_e_puramente_descritivo():
    dados = pd.DataFrame(
        {
            "data_referencia": [dt.date(2025, 1, 1), dt.date(2025, 2, 1), dt.date(2025, 1, 1)],
            "unidade": ["3550308", "3550308", "3304557"],
            "variavel": ["saldo_credito_pf"] * 3,
            "valor": [100.0, 200.0, 50.0],
        }
    )

    resumo = caracterizar_municipios(dados)

    linha_sp = resumo.loc[("3550308", "saldo_credito_pf")]
    assert linha_sp["media"] == pytest.approx(150.0)
    assert linha_sp["valor_mais_recente"] == pytest.approx(200.0)
    assert linha_sp["data_mais_recente"] == dt.date(2025, 2, 1)


def test_caracterizar_municipios_com_dados_vazios_retorna_dataframe_vazio():
    resultado = caracterizar_municipios(pd.DataFrame(columns=["data_referencia", "unidade", "variavel", "valor"]))
    assert resultado.empty
