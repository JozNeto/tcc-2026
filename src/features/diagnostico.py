"""Diagnóstico exploratório: estacionariedade, decomposição sazonal e correlação
cruzada com defasagens (spec 02, seção "Decomposição e diagnóstico").

Implementa `specs/02-limpeza-eda/spec.md`, critério 2: para cada série do núcleo
nacional, produz decomposição sazonal, testes de estacionariedade e correlação
cruzada com defasagens de 0 a 12 meses contra o indicador de exposição a apostas.
"""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.seasonal import DecomposeResult, seasonal_decompose
from statsmodels.tsa.stattools import adfuller, kpss

OBSERVACOES_MINIMAS_DECOMPOSICAO = 24


class SerieCurtaDemaisError(Exception):
    """Levantado quando uma série tem menos de `OBSERVACOES_MINIMAS_DECOMPOSICAO`
    observações — spec 02, "Casos de borda": não força decomposição instável."""


def avaliar_estacionariedade(serie: pd.Series) -> dict:
    """Roda ADF (H0: raiz unitária / não-estacionária) e KPSS (H0: estacionária) e
    retorna o resultado bruto de cada teste — a interpretação (estacionária ou não)
    fica explícita nas duas hipóteses nulas opostas, nunca resumida a um único booleano
    sem contexto (specs/02-limpeza-eda/spec.md, critério 2: "resultado, não apenas a
    conclusão binária")."""
    serie_limpa = serie.dropna()

    adf_estatistica, adf_p_valor, *_ = adfuller(serie_limpa, autolag="AIC")
    kpss_estatistica, kpss_p_valor, *_ = kpss(serie_limpa, regression="c", nlags="auto")

    return {
        "adf_estatistica": adf_estatistica,
        "adf_p_valor": adf_p_valor,
        "adf_rejeita_raiz_unitaria_5pct": bool(adf_p_valor < 0.05),
        "kpss_estatistica": kpss_estatistica,
        "kpss_p_valor": kpss_p_valor,
        "kpss_rejeita_estacionariedade_5pct": bool(kpss_p_valor < 0.05),
        "n_observacoes": len(serie_limpa),
    }


def decompor_sazonalidade(serie: pd.Series, periodo: int = 12, modelo: str = "additive") -> DecomposeResult:
    """Decompõe a série em tendência, sazonalidade e resíduo.

    Raises:
        SerieCurtaDemaisError: se a série tiver menos de
            `OBSERVACOES_MINIMAS_DECOMPOSICAO` observações não-nulas (menos de 2
            ciclos sazonais completos) — quem chama deve tratar isso como um
            resultado válido de diagnóstico ("sazonalidade não avaliável"), não como
            falha do pipeline.
    """
    serie_limpa = serie.dropna()
    if len(serie_limpa) < OBSERVACOES_MINIMAS_DECOMPOSICAO:
        raise SerieCurtaDemaisError(
            f"série tem {len(serie_limpa)} observações, mínimo é "
            f"{OBSERVACOES_MINIMAS_DECOMPOSICAO} para decomposição sazonal confiável"
        )
    return seasonal_decompose(serie_limpa, model=modelo, period=periodo)


def correlacao_cruzada_defasagens(
    serie_resposta: pd.Series, serie_exogena: pd.Series, max_defasagem: int = 12
) -> pd.DataFrame:
    """Correlação de Pearson entre `serie_resposta[t]` e `serie_exogena[t - defasagem]`,
    para `defasagem` de 0 a `max_defasagem` meses.

    Returns:
        DataFrame com colunas `defasagem`, `correlacao`, `n_observacoes_pareadas`.
    """
    linhas = []
    for defasagem in range(max_defasagem + 1):
        exogena_defasada = serie_exogena.shift(defasagem)
        pareado = pd.concat([serie_resposta, exogena_defasada], axis=1, join="inner").dropna()
        correlacao = pareado.iloc[:, 0].corr(pareado.iloc[:, 1]) if len(pareado) > 1 else float("nan")
        linhas.append({"defasagem": defasagem, "correlacao": correlacao, "n_observacoes_pareadas": len(pareado)})
    return pd.DataFrame(linhas)


def diagnosticar(
    serie: pd.Series,
    serie_exogena: pd.Series | None = None,
    periodo_sazonal: int = 12,
    max_defasagem: int = 12,
) -> dict:
    """Orquestra o diagnóstico completo de uma série do núcleo nacional.

    Returns:
        Dict com `estacionariedade` (ver `avaliar_estacionariedade`),
        `decomposicao_disponivel` (bool), `decomposicao` (`DecomposeResult` ou `None`
        se a série for curta demais — ver `SerieCurtaDemaisError`), `aviso_decomposicao`
        (`str | None`) e, se `serie_exogena` for informada, `correlacao_cruzada`
        (ver `correlacao_cruzada_defasagens`).
    """
    resultado: dict = {"estacionariedade": avaliar_estacionariedade(serie)}

    try:
        resultado["decomposicao"] = decompor_sazonalidade(serie, periodo=periodo_sazonal)
        resultado["decomposicao_disponivel"] = True
        resultado["aviso_decomposicao"] = None
    except SerieCurtaDemaisError as exc:
        resultado["decomposicao"] = None
        resultado["decomposicao_disponivel"] = False
        resultado["aviso_decomposicao"] = str(exc)

    if serie_exogena is not None:
        resultado["correlacao_cruzada"] = correlacao_cruzada_defasagens(serie, serie_exogena, max_defasagem)

    return resultado
