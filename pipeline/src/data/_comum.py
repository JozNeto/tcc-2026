"""Utilitários compartilhados por todos os módulos de `src/data/`.

Não é um módulo de coleta por si só — nenhuma fonte específica deve ser adicionada
aqui, apenas lógica reaproveitável entre fontes (contrato de saída, truncamento por
data de corte, leitura de exportações manuais oficiais).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

COLUNAS_SAIDA = ("data_referencia", "unidade", "variavel", "valor", "fonte", "coletado_em")


class ArquivoExportacaoAusenteError(Exception):
    """Levantado quando uma fonte sem API oficial estável espera um arquivo
    exportado manualmente que ainda não foi colocado em
    `data/raw/`."""


def montar_long(
    datas: list[dt.date] | pd.Series,
    valores: list[float] | pd.Series,
    variavel: str,
    unidade: str,
    fonte: str,
    coletado_em: dt.datetime,
) -> pd.DataFrame:
    """Monta um DataFrame no contrato long-format do projeto."""
    return pd.DataFrame(
        {
            "data_referencia": list(datas),
            "unidade": unidade,
            "variavel": variavel,
            "valor": list(valores),
            "fonte": fonte,
            "coletado_em": coletado_em,
        }
    )[list(COLUNAS_SAIDA)]


def filtrar_data_corte(
    df: pd.DataFrame, data_corte: dt.date, coluna: str = "data_referencia"
) -> pd.DataFrame:
    """Trunca `df` na data de corte do projeto."""
    if df.empty:
        return df
    return df[df[coluna] <= data_corte].reset_index(drop=True)


def ler_planilha_exportada(
    caminho: Path,
    coluna_data_origem: str,
    coluna_valor_origem: str,
    variavel: str,
    unidade: str,
    fonte: str,
    data_corte: dt.date,
    unidade_coluna_origem: str | None = None,
) -> pd.DataFrame:
    """Lê uma exportação manual oficial (CSV/XLSX) e converte para o contrato
    long-format do projeto.

    Usada por fontes sem API oficial estável. O arquivo deve ser colocado manualmente em `data/raw/`
    por um integrante do grupo, exportado diretamente da interface oficial da
    fonte (nunca de terceiros).

    Args:
        caminho: caminho do arquivo CSV/XLSX exportado.
        coluna_data_origem: nome da coluna de data no arquivo original.
        coluna_valor_origem: nome da coluna de valor no arquivo original.
        variavel: nome canônico da variável de saída.
        unidade: `"BR"`, sigla de UF ou código IBGE do município.
        fonte: identificador da fonte para a coluna `fonte` da saída.
        data_corte: ver `filtrar_data_corte`.
        unidade_coluna_origem: se a planilha tiver uma coluna com a unidade
            (ex.: sigla de UF por linha), usar essa coluna em vez do parâmetro fixo
            `unidade`.

    Raises:
        ArquivoExportacaoAusenteError: se `caminho` não existir.
    """
    if not caminho.exists():
        raise ArquivoExportacaoAusenteError(
            f"exportação manual esperada em '{caminho}' não foi encontrada — "
            "ver docstring do módulo de coleta para instruções de como obtê-la."
        )

    leitor = pd.read_excel if caminho.suffix.lower() in (".xlsx", ".xls") else pd.read_csv
    bruto = leitor(caminho)

    coletado_em = dt.datetime.now(dt.timezone.utc)
    df = montar_long(
        datas=pd.to_datetime(bruto[coluna_data_origem]).dt.date,
        valores=pd.to_numeric(bruto[coluna_valor_origem], errors="coerce"),
        variavel=variavel,
        unidade=(bruto[unidade_coluna_origem] if unidade_coluna_origem else unidade),
        fonte=fonte,
        coletado_em=coletado_em,
    )
    return filtrar_data_corte(df, data_corte)
