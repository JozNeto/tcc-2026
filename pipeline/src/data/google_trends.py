"""Ingestão do Google Trends (spec 01, camadas Recortes 1 e 2): principal insumo do
indicador composto de exposição territorial (docs/00-proposta-resumo.md, seção 5).

**Exportação manual oficial, não scraping, não `pytrends`.** trends.google.com não
tem API pública, mas a própria interface oferece um botão nativo "Fazer download"
que gera um CSV oficial — usar esse botão é a via decidida pelo grupo (ver
docs/adr/0001-registro-inicial.md, decisão 4: evitar scraping ao máximo). Isso
também descarta a necessidade de `pytrends` (biblioteca não-oficial que faz scraping
por baixo dos panos) cogitada inicialmente na proposta.

Este módulo lê diretamente o CSV nativo exportado pelo Google Trends, nos dois
formatos que a interface produz:

- **Regional** ("Interesse por sub-região"): 1ª linha em branco/metadados, 2ª linha
  cabeçalho `Região,<termo>: (<período>)`, linhas seguintes `<UF ou cidade>,<0-100>`.
  Uso principal do projeto — comparar UFs/municípios (Recortes 1 e 2).
- **Temporal** ("Interesse ao longo do tempo"): 1ª linha `Categoria: ...`, linha em
  branco, cabeçalho `Semana,<termo>: (<região>)` ou `Mês,...`, linhas seguintes
  `<data>,<0-100>`.

Os valores do Google Trends são um índice relativo de 0 a 100 **normalizado por
consulta** — comparar números de consultas/exportações diferentes sem um termo âncora
comum não é válido (specs/01-ingestao-dados/spec.md, "Casos de borda"). Este módulo
não resolve isso sozinho: a normalização entre exportações é responsabilidade de
`src/features/indicador_territorial.py` (spec 02), que deve usar um termo âncora
comum entre todas as consultas territoriais.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.data._comum import COLUNAS_SAIDA, filtrar_data_corte

FONTE = "Google Trends (exportação manual CSV)"
VARIAVEL = "google_trends_interesse_apostas"


class ExportacaoGoogleTrendsInvalidaError(Exception):
    """Levantado quando o CSV não corresponde a nenhum dos dois formatos nativos
    conhecidos de exportação do Google Trends."""


def _linha_cabecalho(linhas: list[str]) -> int:
    for indice, linha in enumerate(linhas):
        if linha.startswith(("Região,", "Semana,", "Mês,", "Dia,")):
            return indice
    raise ExportacaoGoogleTrendsInvalidaError(
        "cabeçalho nativo do Google Trends não encontrado (esperado 'Região,...', "
        "'Semana,...', 'Mês,...' ou 'Dia,...')"
    )


def coletar_regional(
    caminho: Path, data_referencia: dt.date, data_corte: dt.date
) -> pd.DataFrame:
    """Lê uma exportação "Interesse por sub-região" (Recortes 1 e 2).

    O Google Trends não anexa uma data por linha nesse formato — o resultado é um
    retrato agregado do período consultado na interface. `data_referencia` é
    informado explicitamente por quem chama (deve corresponder ao período realmente
    usado na consulta feita no navegador).

    Args:
        caminho: caminho do CSV exportado.
        data_referencia: data a atribuir a todas as linhas (fim do período consultado).
        data_corte: ver specs/constitution.md §3.

    Returns:
        DataFrame long-format, `unidade` = nome da UF/cidade como aparece no export
        (harmonização de nomes para sigla/código IBGE é responsabilidade de
        `src/features/indicador_territorial.py`).
    """
    texto = caminho.read_text(encoding="utf-8")
    linhas = texto.splitlines()
    indice_cabecalho = _linha_cabecalho(linhas)
    if not linhas[indice_cabecalho].startswith("Região,"):
        raise ExportacaoGoogleTrendsInvalidaError(
            f"esperado export regional ('Região,...'), encontrado: {linhas[indice_cabecalho]!r}"
        )

    bruto = pd.read_csv(caminho, skiprows=indice_cabecalho)
    coluna_valor = bruto.columns[1]

    coletado_em = dt.datetime.now(dt.timezone.utc)
    df = pd.DataFrame(
        {
            "data_referencia": data_referencia,
            "unidade": bruto["Região"],
            "variavel": VARIAVEL,
            "valor": pd.to_numeric(bruto[coluna_valor], errors="coerce"),
            "fonte": FONTE,
            "coletado_em": coletado_em,
        }
    )[list(COLUNAS_SAIDA)]

    return filtrar_data_corte(df, data_corte)


def coletar_temporal(caminho: Path, unidade: str, data_corte: dt.date) -> pd.DataFrame:
    """Lê uma exportação "Interesse ao longo do tempo" para uma única unidade
    (ex.: Brasil, ou uma UF específica).

    Args:
        caminho: caminho do CSV exportado.
        unidade: unidade a que esta série corresponde ("BR", sigla de UF, etc.) —
            informado por quem chama, pois o CSV nativo não traz essa informação
            de forma estruturada (aparece só no nome do termo pesquisado).
        data_corte: ver specs/constitution.md §3.
    """
    texto = caminho.read_text(encoding="utf-8")
    linhas = texto.splitlines()
    indice_cabecalho = _linha_cabecalho(linhas)
    if not linhas[indice_cabecalho].startswith(("Semana,", "Mês,", "Dia,")):
        raise ExportacaoGoogleTrendsInvalidaError(
            f"esperado export temporal ('Semana,...'/'Mês,...'/'Dia,...'), "
            f"encontrado: {linhas[indice_cabecalho]!r}"
        )

    bruto = pd.read_csv(caminho, skiprows=indice_cabecalho)
    coluna_data, coluna_valor = bruto.columns[0], bruto.columns[1]

    coletado_em = dt.datetime.now(dt.timezone.utc)
    df = pd.DataFrame(
        {
            "data_referencia": pd.to_datetime(bruto[coluna_data]).dt.date,
            "unidade": unidade,
            "variavel": VARIAVEL,
            "valor": pd.to_numeric(bruto[coluna_valor], errors="coerce"),
            "fonte": FONTE,
            "coletado_em": coletado_em,
        }
    )[list(COLUNAS_SAIDA)]

    return filtrar_data_corte(df, data_corte)
