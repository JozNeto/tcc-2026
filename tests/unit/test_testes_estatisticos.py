from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.testes_estatisticos import (
    EstatisticaError,
    calcular_diebold_mariano,
    corrigir_bonferroni,
)


def test_detecta_modelo_1_significativamente_melhor():
    rng = np.random.default_rng(0)
    erro_modelo_1 = rng.normal(0, 0.1, size=60)  # erros pequenos
    erro_modelo_2 = rng.normal(0, 5.0, size=60)  # erros grandes

    resultado = calcular_diebold_mariano(erro_modelo_1, erro_modelo_2)

    assert resultado["modelo_1_melhor"] is True
    assert resultado["diferenca_significativa_5pct"] is True
    assert resultado["p_valor"] < 0.05


def test_modelos_com_erro_similar_nao_e_significativo():
    rng = np.random.default_rng(1)
    erro_modelo_1 = rng.normal(0, 1.0, size=60)
    erro_modelo_2 = rng.normal(0, 1.0, size=60)

    resultado = calcular_diebold_mariano(erro_modelo_1, erro_modelo_2)

    assert resultado["p_valor"] > 0.05
    assert resultado["diferenca_significativa_5pct"] is False


def test_levanta_erro_com_tamanhos_diferentes():
    with pytest.raises(EstatisticaError):
        calcular_diebold_mariano([1, 2, 3], [1, 2])


def test_levanta_erro_com_poucas_observacoes():
    with pytest.raises(EstatisticaError):
        calcular_diebold_mariano([1], [2])


def test_levanta_erro_com_variancia_zero():
    # d_t = e1^2 - e2^2 é constante em todos os pontos -> variância zero
    with pytest.raises(EstatisticaError):
        calcular_diebold_mariano([1, 1, 1, 1], [2, 2, 2, 2])


def test_levanta_erro_com_funcao_perda_desconhecida():
    with pytest.raises(EstatisticaError):
        calcular_diebold_mariano([1, 2, 3], [2, 3, 1], funcao_perda="log")


def test_funciona_com_horizonte_maior_que_1():
    rng = np.random.default_rng(2)
    erro_modelo_1 = rng.normal(0, 0.5, size=40)
    erro_modelo_2 = rng.normal(0, 0.5, size=40)
    resultado = calcular_diebold_mariano(erro_modelo_1, erro_modelo_2, h=3)
    assert "estatistica_dm" in resultado


def test_corrigir_bonferroni_multiplica_pelo_numero_de_testes():
    resultado = corrigir_bonferroni([0.01, 0.02, 0.5])
    assert resultado == pytest.approx([0.03, 0.06, 1.0])


def test_corrigir_bonferroni_limita_em_1():
    resultado = corrigir_bonferroni([0.5, 0.6])
    assert resultado == pytest.approx([1.0, 1.0])
