"""Checagens de plausibilidade do indicador composto territorial.

**Isto não é validação estatística de acurácia.** Não existe estatística oficial
desagregada por UF/município para comparar o indicador composto — as funções aqui checam plausibilidade
indireta (correlação com proxies conhecidos, estabilidade do ranking a pequenas
mudanças de peso), nunca "acurácia" ou "p-valor de validade" do indicador em si.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.indicador_territorial import construir_indicador_composto

LIMIAR_ESTABILIDADE_SPEARMAN = 0.7


class ValidacaoTerritorialError(Exception):
    """Levantado quando não há dados pareados suficientes para uma checagem."""


def checar_correlacao_com_proxy(indicador_composto: pd.Series, proxy: pd.Series) -> dict:
    """Correlação de Pearson entre o indicador composto e uma variável proxy
    conhecida (ex.: renda per capita, população, taxa de bancarização). Uma
    correlação no sentido esperado é evidência de plausibilidade — **não** prova que
    o indicador mede exposição real a apostas com acurácia.

    Raises:
        ValidacaoTerritorialError: se houver menos de 3 unidades territoriais
            pareadas entre as duas séries.
    """
    pareado = pd.concat([indicador_composto, proxy], axis=1, join="inner").dropna()
    if len(pareado) < 3:
        raise ValidacaoTerritorialError(
            f"apenas {len(pareado)} unidades territoriais pareadas — mínimo é 3 para uma correlação minimamente informativa"
        )

    correlacao = float(pareado.iloc[:, 0].corr(pareado.iloc[:, 1]))
    return {"correlacao": correlacao, "n_unidades_pareadas": len(pareado)}


def checar_estabilidade_a_pesos(
    componentes: dict[str, pd.Series],
    pesos_base: dict[str, float],
    perturbacao: float = 0.1,
    n_perturbacoes: int = 20,
    seed: int = 42,
) -> dict:
    """Recalcula o indicador composto com os pesos perturbados aleatoriamente (até
    `± perturbacao`, proporcional ao peso original) e mede, via correlação de
    Spearman entre o ranking original e cada ranking perturbado, quão sensível o
    ordenamento de UFs é à escolha exata dos pesos.

    Seed sempre fixa.

    Returns:
        Dict com `correlacao_spearman_media`, `correlacao_spearman_minima`,
        `n_perturbacoes`, `seed` e `estavel` (`True` se a correlação mínima observada
        superar `LIMIAR_ESTABILIDADE_SPEARMAN` — limiar documentado, não um teste de
        significância formal).
    """
    rng = np.random.default_rng(seed)
    ranking_base = construir_indicador_composto(componentes, pesos_base)["indicador_composto"].rank()

    correlacoes = []
    for _ in range(n_perturbacoes):
        pesos_perturbados = {
            nome: max(0.01, peso * (1 + rng.uniform(-perturbacao, perturbacao))) for nome, peso in pesos_base.items()
        }
        ranking_perturbado = construir_indicador_composto(componentes, pesos_perturbados)["indicador_composto"].rank()
        correlacoes.append(ranking_base.corr(ranking_perturbado, method="spearman"))

    return {
        "correlacao_spearman_media": float(np.mean(correlacoes)),
        "correlacao_spearman_minima": float(np.min(correlacoes)),
        "n_perturbacoes": n_perturbacoes,
        "seed": seed,
        "estavel": bool(np.min(correlacoes) > LIMIAR_ESTABILIDADE_SPEARMAN),
    }
