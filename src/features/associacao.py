"""Testes de associação usados na pergunta central (série temporal e corte transversal).

Nenhuma função aqui estabelece causalidade: medem associação estatística, e o texto que
consome estes resultados deve dizê-lo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests


class AssociacaoError(Exception):
    """Entrada insuficiente ou incompatível para o teste."""


def regressao_defasada_hac(
    y: pd.Series, x: pd.Series, controles: pd.DataFrame | None, defasagem: int, maxlags: int = 6
) -> dict:
    """Regride Δy_t em Δx_{t-defasagem} (+ Δcontroles_t), erros-padrão HAC (Newey-West).

    Séries em nível são diferenciadas aqui (primeira diferença), para evitar regressão
    espúria entre séries não estacionárias.
    """
    dados = pd.DataFrame({"dy": y.diff(), "dx": x.diff().shift(defasagem)})
    if controles is not None:
        dados = dados.join(controles.diff().add_prefix("c_"))
    dados = dados.dropna()
    if len(dados) < 24:
        raise AssociacaoError(f"apenas {len(dados)} observações após diferenciar/defasar (mínimo 24)")
    if dados["dx"].nunique() < 8:
        raise AssociacaoError("regressor com menos de 8 valores distintos (série esparsa) — resultado não confiável")
    dados["dx"] = (dados["dx"] - dados["dx"].mean()) / dados["dx"].std()
    X = sm.add_constant(dados.drop(columns="dy"))
    modelo = sm.OLS(dados["dy"], X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    ols = sm.OLS(dados["dy"], X).fit()
    base = sm.OLS(dados["dy"], X.drop(columns="dx")).fit()
    # Inferência HAC pode ser otimista em amostras pequenas: usa-se o MAIOR entre o p-valor
    # HAC e o de MQO comum (conservador).
    p_hac, p_ols = float(modelo.pvalues["dx"]), float(ols.pvalues["dx"])
    return {
        "defasagem": defasagem,
        "coef_por_desvio_padrao": float(modelo.params["dx"]),
        "erro_padrao": float(modelo.bse["dx"]),
        "p_hac": p_hac,
        "p_ols": p_ols,
        "p_valor": max(p_hac, p_ols),
        "n": int(modelo.nobs),
        "r2": float(modelo.rsquared),
        "delta_r2": float(modelo.rsquared - base.rsquared),
    }


def granger(y: pd.Series, x: pd.Series, maxlag: int = 6) -> dict:
    """Teste de Granger de x → y sobre primeiras diferenças; retorna o menor p-valor (F) entre
    as defasagens 1..maxlag e a defasagem correspondente (a ser corrigido por comparações
    múltiplas por quem chama)."""
    dados = pd.DataFrame({"y": y.diff(), "x": x.diff()}).dropna()
    if len(dados) < 3 * maxlag + 10:
        raise AssociacaoError("série curta demais para Granger com esse maxlag")
    res = grangercausalitytests(dados[["y", "x"]], maxlag=maxlag)
    ps = {lag: float(res[lag][0]["ssr_ftest"][1]) for lag in range(1, maxlag + 1)}
    melhor = min(ps, key=ps.get)
    return {"menor_p": ps[melhor], "defasagem": melhor, "p_por_defasagem": ps, "n": len(dados)}


def spearman(a: pd.Series, b: pd.Series) -> dict:
    """Correlação de Spearman entre duas séries alinhadas pelo índice."""
    par = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(par) < 8:
        raise AssociacaoError(f"apenas {len(par)} pares — mínimo 8")
    rho, p = stats.spearmanr(par.iloc[:, 0], par.iloc[:, 1])
    return {"rho": float(rho), "p_valor": float(p), "n": len(par)}


def normalizar_min_max(s: pd.Series) -> pd.Series:
    if s.max() == s.min():
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def bonferroni(p_valores: list[float]) -> list[float]:
    n = len(p_valores)
    return [float(min(p * n, 1.0)) for p in p_valores]


def padronizar(s: pd.Series) -> pd.Series:
    desvio = s.std()
    if not desvio or np.isnan(desvio):
        raise AssociacaoError("série constante — não dá para padronizar")
    return (s - s.mean()) / desvio
