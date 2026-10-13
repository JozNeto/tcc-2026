from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features import associacao as a


def _serie_com_relacao(defasagem: int, n: int = 120, seed: int = 0) -> tuple[pd.Series, pd.Series]:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-01", periods=n, freq="MS")
    dx = rng.normal(size=n)
    dy = np.roll(dx, defasagem) * 0.8 + rng.normal(scale=0.3, size=n)
    return pd.Series(np.cumsum(dy), index=idx), pd.Series(np.cumsum(dx), index=idx)


def test_regressao_detecta_relacao_na_defasagem_correta():
    y, x = _serie_com_relacao(defasagem=3)
    certo = a.regressao_defasada_hac(y, x, None, defasagem=3)
    errado = a.regressao_defasada_hac(y, x, None, defasagem=1)
    assert certo["p_valor"] < 0.001
    assert certo["coef_por_desvio_padrao"] > 0.5
    assert certo["delta_r2"] > 0.3
    assert errado["p_valor"] > 0.01


def test_regressao_sem_relacao_nao_e_significativa():
    rng = np.random.default_rng(5)
    idx = pd.date_range("2015-01-01", periods=120, freq="MS")
    y = pd.Series(np.cumsum(rng.normal(size=120)), index=idx)
    x = pd.Series(np.cumsum(rng.normal(size=120)), index=idx)
    assert a.regressao_defasada_hac(y, x, None, defasagem=0)["p_valor"] > 0.01


def test_regressao_levanta_erro_com_poucas_observacoes():
    idx = pd.date_range("2020-01-01", periods=15, freq="MS")
    s = pd.Series(range(15), index=idx, dtype=float)
    with pytest.raises(a.AssociacaoError):
        a.regressao_defasada_hac(s, s, None, defasagem=2)


def test_granger_encontra_precedencia():
    y, x = _serie_com_relacao(defasagem=2)
    r = a.granger(y, x, maxlag=4)
    assert r["menor_p"] < 0.001
    assert r["defasagem"] in (2, 3, 4)


def test_spearman_monotonica_perfeita():
    s = pd.Series(range(10), index=list("abcdefghij"), dtype=float)
    r = a.spearman(s, s**2)
    assert r["rho"] == pytest.approx(1.0)


def test_spearman_com_poucos_pares_levanta_erro():
    with pytest.raises(a.AssociacaoError):
        a.spearman(pd.Series([1, 2, 3]), pd.Series([1, 2, 3]))


def test_bonferroni_limita_em_1():
    assert a.bonferroni([0.01, 0.6]) == pytest.approx([0.02, 1.0])


def test_padronizar_serie_constante_levanta_erro():
    with pytest.raises(a.AssociacaoError):
        a.padronizar(pd.Series([2.0, 2.0, 2.0]))
