from __future__ import annotations

import pytest

from src.models.custo_patrimonial import simular_custo_patrimonial


def test_mesma_seed_produz_resultado_identico():
    kwargs = {
        "gasto_mensal_redirecionado": 100.0,
        "horizonte_meses": 12,
        "retorno_mensal_esperado": 0.005,
        "retorno_mensal_desvio": 0.02,
        "n_simulacoes": 500,
        "seed": 7,
    }
    resultado_1 = simular_custo_patrimonial(**kwargs)
    resultado_2 = simular_custo_patrimonial(**kwargs)
    assert resultado_1 == resultado_2


def test_seeds_diferentes_produzem_resultados_diferentes():
    kwargs = {
        "gasto_mensal_redirecionado": 100.0,
        "horizonte_meses": 12,
        "retorno_mensal_esperado": 0.005,
        "retorno_mensal_desvio": 0.02,
        "n_simulacoes": 500,
    }
    resultado_1 = simular_custo_patrimonial(seed=1, **kwargs)
    resultado_2 = simular_custo_patrimonial(seed=2, **kwargs)
    assert resultado_1["patrimonio_medio"] != resultado_2["patrimonio_medio"]


def test_sem_retorno_e_sem_desvio_acumula_exatamente_o_total_investido():
    resultado = simular_custo_patrimonial(
        gasto_mensal_redirecionado=100.0,
        horizonte_meses=12,
        retorno_mensal_esperado=0.0,
        retorno_mensal_desvio=0.0,
        n_simulacoes=10,
        seed=0,
    )
    assert resultado["total_investido"] == pytest.approx(1200.0)
    assert resultado["patrimonio_medio"] == pytest.approx(1200.0)
    assert resultado["custo_oportunidade_medio"] == pytest.approx(0.0)


def test_retorno_constante_bate_com_formula_fechada_de_anuidade():
    aporte, r, meses = 100.0, 0.01, 12
    esperado = aporte * (1 + r) * (((1 + r) ** meses - 1) / r)

    resultado = simular_custo_patrimonial(
        gasto_mensal_redirecionado=aporte,
        horizonte_meses=meses,
        retorno_mensal_esperado=r,
        retorno_mensal_desvio=0.0,
        n_simulacoes=5,
        seed=0,
    )

    assert resultado["patrimonio_medio"] == pytest.approx(esperado, rel=1e-9)


def test_resultado_registra_seed_e_parametros_para_rastreabilidade():
    resultado = simular_custo_patrimonial(
        gasto_mensal_redirecionado=164.0,
        horizonte_meses=24,
        retorno_mensal_esperado=0.005,
        retorno_mensal_desvio=0.02,
        n_simulacoes=100,
        seed=99,
    )
    assert resultado["seed"] == 99
    assert resultado["n_simulacoes"] == 100
    assert resultado["horizonte_meses"] == 24
