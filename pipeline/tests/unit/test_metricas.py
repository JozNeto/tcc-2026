"""Testes unitários de src/evaluation/metricas.py — valores calculados à mão para
séries sintéticas pequenas."""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.metricas import (
    MetricaError,
    calcular_mae,
    calcular_mase,
    calcular_rmse,
    calcular_smape,
)


def test_calcular_mae_valor_calculado_a_mao():
    # erros: |1-1|=0, |2-2|=0, |3-5|=2 -> média = 2/3
    assert calcular_mae([1, 2, 3], [1, 2, 5]) == pytest.approx(2 / 3)


def test_calcular_rmse_valor_calculado_a_mao():
    # erros^2: 0, 0, 4 -> média = 4/3 -> raiz = 1.1547...
    assert calcular_rmse([1, 2, 3], [1, 2, 5]) == pytest.approx((4 / 3) ** 0.5)


def test_calcular_smape_valor_calculado_a_mao():
    # (1,1)->0 | (2,2)->0 | (3,5)-> 2*2/(3+5)=0.5 | média*100 = 16.6666...
    assert calcular_smape([1, 2, 3], [1, 2, 5]) == pytest.approx(100 / 6)


def test_calcular_smape_ponto_zero_zero_contribui_zero_nao_nan():
    resultado = calcular_smape([0, 5], [0, 5])
    assert resultado == pytest.approx(0.0)


def test_calcular_mase_valor_calculado_a_mao():
    serie_treino = pd.Series([10, 12, 11, 13, 12, 14])
    # |diffs|: |12-10|=2, |11-12|=1, |13-11|=2, |12-13|=1, |14-12|=2 -> média = 1.6
    # MAE previsão: |15-14|=1, |16-15|=1 -> média = 1
    resultado = calcular_mase([15, 16], [14, 15], serie_treino, periodo_sazonal=1)
    assert resultado == pytest.approx(1 / 1.6)


def test_calcular_mase_levanta_erro_com_serie_treino_constante():
    serie_treino = pd.Series([10, 10, 10, 10])
    with pytest.raises(MetricaError):
        calcular_mase([11, 12], [10, 10], serie_treino)


def test_calcular_mase_com_periodo_sazonal():
    serie_treino = pd.Series([1, 2, 3, 1, 2, 3, 1, 2, 3])
    # diff sazonal (periodo=3) é 0 em todos os pontos (série perfeitamente periódica)
    # -> escala zero -> MASE indefinido
    with pytest.raises(MetricaError):
        calcular_mase([1, 2], [1, 2], serie_treino, periodo_sazonal=3)
