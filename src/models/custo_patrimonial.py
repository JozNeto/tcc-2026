"""Simulação estocástica do custo de oportunidade patrimonial:
patrimônio contrafactual associado ao redirecionamento do gasto médio observado em
apostas para um investimento mensal.

Seed sempre fixa — reprodutibilidade obrigatória: a mesma
seed produz exatamente o mesmo resultado, sempre.
"""

from __future__ import annotations

import numpy as np


def simular_custo_patrimonial(
    gasto_mensal_redirecionado: float,
    horizonte_meses: int,
    retorno_mensal_esperado: float,
    retorno_mensal_desvio: float,
    n_simulacoes: int = 10_000,
    seed: int = 42,
) -> dict:
    """Simula, via Monte Carlo, o patrimônio acumulado se `gasto_mensal_redirecionado`
    fosse investido todo mês, com retorno mensal aleatório `~ Normal(retorno_mensal_esperado,
    retorno_mensal_desvio)`, ao longo de `horizonte_meses`.

    Convenção de acumulação: a cada mês, o aporte entra primeiro, depois o saldo
    inteiro (aporte incluído) rende o retorno do mês —
    `saldo_t = (saldo_{t-1} + aporte) * (1 + retorno_t)`.

    Args:
        gasto_mensal_redirecionado: valor mensal investido (ex.: gasto médio
            observado em apostas, R$).
        horizonte_meses: nº de meses simulados.
        retorno_mensal_esperado: média da distribuição normal de retorno mensal.
        retorno_mensal_desvio: desvio-padrão da distribuição normal de retorno mensal.
        n_simulacoes: nº de trajetórias simuladas.
        seed: seed do gerador de números aleatórios — sempre fixa e registrada no
            resultado, para reprodutibilidade.

    Returns:
        Dict com `seed`, `n_simulacoes`, `horizonte_meses`, `total_investido`,
        `patrimonio_medio`, `patrimonio_mediana`, `patrimonio_p5`, `patrimonio_p95`
        e `custo_oportunidade_medio` (patrimônio médio menos total investido, ou
        seja, o ganho médio atribuível apenas ao retorno do investimento).
    """
    rng = np.random.default_rng(seed)
    retornos = rng.normal(retorno_mensal_esperado, retorno_mensal_desvio, size=(n_simulacoes, horizonte_meses))

    saldo = np.zeros(n_simulacoes)
    for mes in range(horizonte_meses):
        saldo = (saldo + gasto_mensal_redirecionado) * (1 + retornos[:, mes])

    total_investido = gasto_mensal_redirecionado * horizonte_meses

    return {
        "seed": seed,
        "n_simulacoes": n_simulacoes,
        "horizonte_meses": horizonte_meses,
        "total_investido": float(total_investido),
        "patrimonio_medio": float(saldo.mean()),
        "patrimonio_mediana": float(np.median(saldo)),
        "patrimonio_p5": float(np.percentile(saldo, 5)),
        "patrimonio_p95": float(np.percentile(saldo, 95)),
        "custo_oportunidade_medio": float(saldo.mean() - total_investido),
    }
