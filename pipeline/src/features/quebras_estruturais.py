"""Detecção de quebras estruturais e confronto com o calendário regulatório
.

Implementa
§2: o detector nunca recebe as datas regulatórias como entrada — elas só entram na
etapa separada de confronto (`confrontar_com_calendario_regulatorio`), que é o
"teste de validade externa da base".
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import ruptures as rpt

# Marcos regulatórios do projeto — usados
# SOMENTE no confronto pós-detecção, nunca como entrada do algoritmo de segmentação.
CALENDARIO_REGULATORIO = {
    "regulamentacao_mercado": dt.date(2025, 1, 1),
    "restricao_beneficiarios": dt.date(2025, 10, 1),
    "suspensao_parcial_judicial": dt.date(2025, 12, 1),
}


def detectar_quebras(
    serie: pd.Series,
    n_quebras: int | None = None,
    penalidade: float = 10.0,
    modelo: str = "rbf",
) -> list:
    """Detecta pontos de quebra estrutural na série, sem qualquer informação prévia
    de datas regulatórias.

    Args:
        serie: série indexada por `data_referencia`, sem NaNs internos relevantes
            (valores ausentes são descartados antes da detecção).
        n_quebras: se informado, usa `ruptures.Binseg` para encontrar exatamente esse
            número de quebras (útil quando se sabe quantas quebras procurar, ex.: em
            teste com série sintética). Se `None`, usa `ruptures.Pelt` com
            `penalidade` para detectar automaticamente quantas quebras existem —
            modo padrão para séries reais, onde o número de quebras é desconhecido.
        penalidade: usada apenas quando `n_quebras` é `None` (modo Pelt). Penalidade
            maior → menos quebras detectadas. Não há valor universalmente correto;
            calibrar por série e documentar se o valor padrão não servir.
        modelo: modelo de custo do `ruptures` (ver documentação da biblioteca).

    Returns:
        Lista de datas (mesmo tipo do índice de `serie`) onde uma quebra foi detectada.
    """
    serie_limpa = serie.dropna()
    valores = serie_limpa.to_numpy().reshape(-1, 1)

    if n_quebras is not None:
        algoritmo = rpt.Binseg(model=modelo).fit(valores)
        pontos = algoritmo.predict(n_bkps=n_quebras)
    else:
        algoritmo = rpt.Pelt(model=modelo).fit(valores)
        pontos = algoritmo.predict(pen=penalidade)

    pontos_quebra = pontos[:-1]  # o último ponto retornado pelo ruptures é o fim da série, não uma quebra
    return [serie_limpa.index[i] for i in pontos_quebra]


def confrontar_com_calendario_regulatorio(
    datas_quebra: list,
    calendario: dict[str, dt.date] | None = None,
    tolerancia_dias: int = 45,
) -> pd.DataFrame:
    """Confronta as quebras detectadas com o calendário regulatório do projeto —
    a etapa de validação externa de validação externa. Esta função nunca é chamada
    pelo detector; é sempre uma etapa posterior e separada.

    Args:
        datas_quebra: saída de `detectar_quebras`.
        calendario: mapeamento nome do marco -> data; usa `CALENDARIO_REGULATORIO`
            se não informado.
        tolerancia_dias: distância máxima, em dias, para considerar que uma quebra
            "coincide" com um marco regulatório.

    Returns:
        DataFrame com uma linha por marco: `marco`, `data_marco`,
        `quebra_mais_proxima`, `distancia_dias`, `coincide_dentro_da_tolerancia`.
    """
    calendario = calendario or CALENDARIO_REGULATORIO
    linhas = []
    for nome_marco, data_marco in calendario.items():
        if datas_quebra:
            mais_proxima = min(datas_quebra, key=lambda data: abs((data - data_marco).days))
            distancia = abs((mais_proxima - data_marco).days)
        else:
            mais_proxima, distancia = None, None

        linhas.append(
            {
                "marco": nome_marco,
                "data_marco": data_marco,
                "quebra_mais_proxima": mais_proxima,
                "distancia_dias": distancia,
                "coincide_dentro_da_tolerancia": distancia is not None and distancia <= tolerancia_dias,
            }
        )
    return pd.DataFrame(linhas)
