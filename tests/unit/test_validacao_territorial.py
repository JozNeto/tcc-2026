from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.validacao_territorial import (
    ValidacaoTerritorialError,
    checar_correlacao_com_proxy,
    checar_estabilidade_a_pesos,
)


def test_checar_correlacao_com_proxy_detecta_correlacao_perfeita():
    indicador = pd.Series({"SP": 1.0, "RJ": 2.0, "BA": 3.0, "AC": 4.0})
    proxy = indicador * 2  # perfeitamente correlacionado

    resultado = checar_correlacao_com_proxy(indicador, proxy)

    assert resultado["correlacao"] == pytest.approx(1.0)
    assert resultado["n_unidades_pareadas"] == 4


def test_checar_correlacao_com_proxy_levanta_erro_com_poucas_unidades():
    indicador = pd.Series({"SP": 1.0, "RJ": 2.0})
    proxy = pd.Series({"SP": 1.0, "RJ": 2.0})
    with pytest.raises(ValidacaoTerritorialError):
        checar_correlacao_com_proxy(indicador, proxy)


def test_checar_correlacao_com_proxy_pareia_apenas_unidades_em_comum():
    indicador = pd.Series({"SP": 1.0, "RJ": 2.0, "BA": 3.0, "MG": 4.0})
    proxy = pd.Series({"SP": 1.0, "RJ": 2.0, "BA": 3.0, "PR": 9.0})  # MG e PR não coincidem
    resultado = checar_correlacao_com_proxy(indicador, proxy)
    assert resultado["n_unidades_pareadas"] == 3


def test_checar_estabilidade_a_pesos_com_componente_unico_e_sempre_estavel():
    """Com um único componente, o ranking não pode mudar com a perturbação de peso
    (perturbar o único peso não altera a ordem relativa das UFs)."""
    componentes = {"a": pd.Series({"SP": 10.0, "RJ": 50.0, "BA": 30.0, "AC": 5.0})}
    resultado = checar_estabilidade_a_pesos(componentes, pesos_base={"a": 1.0}, n_perturbacoes=10, seed=1)

    assert resultado["correlacao_spearman_minima"] == pytest.approx(1.0)
    assert resultado["estavel"] is True


def test_checar_estabilidade_a_pesos_mesma_seed_reproduz_resultado():
    componentes = {
        "a": pd.Series({"SP": 10.0, "RJ": 50.0, "BA": 30.0, "AC": 5.0}),
        "b": pd.Series({"SP": 40.0, "RJ": 5.0, "BA": 60.0, "AC": 90.0}),
    }
    kwargs = {"pesos_base": {"a": 1.0, "b": 1.0}, "n_perturbacoes": 15, "seed": 7}

    resultado_1 = checar_estabilidade_a_pesos(componentes, **kwargs)
    resultado_2 = checar_estabilidade_a_pesos(componentes, **kwargs)

    assert resultado_1 == resultado_2
