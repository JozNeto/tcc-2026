"""Métricas de erro para comparação de modelos.

MASE/sMAPE são as métricas de decisão principais (erro relativo — as séries do
projeto têm escalas muito diferentes, ver docs/tdd.md, seção 4); RMSE/MAE ficam como
leitura complementar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class MetricaError(Exception):
    """Levantado quando uma métrica fica matematicamente indefinida (ex.: MASE com
    série de treino constante) — nunca retorna `NaN` silencioso nesse caso
."""


def calcular_mae(valor_real, valor_previsto) -> float:
    return float(np.mean(np.abs(np.asarray(valor_real, dtype=float) - np.asarray(valor_previsto, dtype=float))))


def calcular_rmse(valor_real, valor_previsto) -> float:
    erro = np.asarray(valor_real, dtype=float) - np.asarray(valor_previsto, dtype=float)
    return float(np.sqrt(np.mean(erro**2)))


def calcular_smape(valor_real, valor_previsto) -> float:
    """sMAPE em %, com a convenção usual de que um ponto onde `real == previsto == 0`
    contribui 0 (em vez de indefinido 0/0)."""
    real = np.asarray(valor_real, dtype=float)
    previsto = np.asarray(valor_previsto, dtype=float)
    denominador = np.abs(real) + np.abs(previsto)
    numerador = 2 * np.abs(real - previsto)

    contribuicoes = np.divide(numerador, denominador, out=np.zeros_like(numerador), where=denominador != 0)
    return float(np.mean(contribuicoes) * 100)


def calcular_mase(valor_real, valor_previsto, serie_treino: pd.Series, periodo_sazonal: int = 1) -> float:
    """MASE = MAE da previsão / MAE do naive (sazonal) *in-sample*, calculado sobre
    a série de treino (Hyndman & Koehler, 2006). `periodo_sazonal=1` corresponde ao
    naive não-sazonal; use 12 para escalar contra o naive sazonal mensal.

    Raises:
        MetricaError: se a série de treino for constante (escala igual a zero,
            MASE matematicamente indefinido).
    """
    erro_previsao = calcular_mae(valor_real, valor_previsto)

    serie_treino_limpa = serie_treino.dropna()
    diffs_treino = serie_treino_limpa.diff(periodo_sazonal).dropna().abs()
    escala = float(diffs_treino.mean())

    if escala == 0:
        raise MetricaError(
            "escala do MASE é zero (série de treino constante no período sazonal "
            f"informado, periodo_sazonal={periodo_sazonal}) — MASE fica indefinido"
        )
    return erro_previsao / escala
