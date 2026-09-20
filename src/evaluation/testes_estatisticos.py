"""Teste de diferença de desempenho entre modelos — Diebold-Mariano (spec 04,
critério 1: nenhuma comparação de modelo é válida sem este teste, além da métrica de
erro relativo — constitution §6).
"""

from __future__ import annotations

import numpy as np
from scipy import stats


class EstatisticaError(Exception):
    """Levantado quando o teste recebe entradas incompatíveis ou produz um
    resultado matematicamente indefinido (ex.: variância zero)."""


def calcular_diebold_mariano(
    erro_modelo_1, erro_modelo_2, h: int = 1, funcao_perda: str = "quadratica"
) -> dict:
    """Testa H0: os dois modelos têm a mesma acurácia preditiva esperada, contra
    H1: as acurácias diferem (teste bicaudal), com a correção de pequena amostra de
    Harvey, Leybourne & Newbold (1997).

    Args:
        erro_modelo_1, erro_modelo_2: erros de previsão (real - previsto) pareados
            no tempo, mesmo tamanho.
        h: horizonte de previsão usado para gerar os erros — controla quantas
            defasagens de autocovariância entram na variância HAC da diferença de
            perdas (`h=1` = sem correção de autocorrelação, apropriado para erros
            de previsão de 1 passo).
        funcao_perda: `"quadratica"` (erro²) ou `"absoluta"` (|erro|).

    Returns:
        Dict com `estatistica_dm`, `p_valor`, `diferenca_significativa_5pct`,
        `perda_media_modelo_1`, `perda_media_modelo_2`, `modelo_1_melhor`
        (`True` se a perda média do modelo 1 for menor), `n_observacoes`.

    Raises:
        EstatisticaError: tamanhos diferentes, menos de 2 observações,
            variância da diferença de perdas zero/negativa, ou `funcao_perda`
            desconhecida.
    """
    e1 = np.asarray(erro_modelo_1, dtype=float)
    e2 = np.asarray(erro_modelo_2, dtype=float)

    if e1.shape != e2.shape:
        raise EstatisticaError("erro_modelo_1 e erro_modelo_2 devem ter o mesmo tamanho")

    n_observacoes = len(e1)
    if n_observacoes < 2:
        raise EstatisticaError("teste de Diebold-Mariano requer ao menos 2 observações pareadas")

    if funcao_perda == "quadratica":
        perda = lambda e: e**2
    elif funcao_perda == "absoluta":
        perda = lambda e: np.abs(e)
    else:
        raise EstatisticaError(f"funcao_perda desconhecida: {funcao_perda!r} (use 'quadratica' ou 'absoluta')")

    perda_1, perda_2 = perda(e1), perda(e2)
    d = perda_1 - perda_2
    d_bar = float(d.mean())

    variancia = float(np.var(d, ddof=0))
    for defasagem in range(1, h):
        gamma_k = float(np.mean((d[defasagem:] - d_bar) * (d[:-defasagem] - d_bar)))
        variancia += 2 * gamma_k

    variancia_media = variancia / n_observacoes
    if variancia_media <= 0:
        raise EstatisticaError(
            "variância estimada da diferença de perdas é zero ou negativa — "
            "estatística de Diebold-Mariano fica indefinida"
        )

    estatistica_dm = d_bar / np.sqrt(variancia_media)
    fator_correcao = np.sqrt((n_observacoes + 1 - 2 * h + h * (h - 1) / n_observacoes) / n_observacoes)
    estatistica_corrigida = float(estatistica_dm * fator_correcao)

    p_valor = float(2 * (1 - stats.t.cdf(np.abs(estatistica_corrigida), df=n_observacoes - 1)))

    return {
        "estatistica_dm": estatistica_corrigida,
        "p_valor": p_valor,
        "diferenca_significativa_5pct": p_valor < 0.05,
        "perda_media_modelo_1": float(perda_1.mean()),
        "perda_media_modelo_2": float(perda_2.mean()),
        "modelo_1_melhor": d_bar < 0,
        "n_observacoes": n_observacoes,
    }


def corrigir_bonferroni(p_valores: list[float]) -> list[float]:
    """Correção de Bonferroni para múltiplas comparações (specs/04-avaliacao/spec.md,
    critério 1: "com correção para múltiplas comparações se mais de dois modelos
    forem comparados simultaneamente")."""
    n_testes = len(p_valores)
    return [min(p * n_testes, 1.0) for p in p_valores]
