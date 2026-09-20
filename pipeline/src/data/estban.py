"""Ingestão do ESTBAN/BCB — Estatística Bancária Mensal por município: saldos de crédito e de depósitos de poupança, usados apenas na
caracterização descritiva dos municípios ilustrados.

**Sem URL de download direta confirmada com segurança.** O BCB disponibiliza o ESTBAN
por município no site institucional, mas a verificação em 2026-08-17 não confirmou um padrão de
URL estável o suficiente para consumo programático sem risco de quebrar
silenciosamente. Como o ESTBAN alimenta só o Recorte 2, o custo de errar essa fonte por adivinhação
é desproporcional ao benefício: este módulo lê um arquivo baixado manualmente do
site oficial do BCB e colocado em `data/raw/estban/`.

Formato esperado do arquivo normalizado (CSV ou XLSX), colunas:
    data              : data de referência do mês
    municipio_ibge    : código IBGE do município (7 dígitos)
    variavel          : um de {"saldo_credito_pf", "saldo_poupanca"}
    valor             : valor em R$

Antes de uma nova rodada de coleta, reavaliar se vale a pena investir em um cliente
HTTP direto (ex.: se o BCB publicar os arquivos ESTBAN em uma URL com padrão estável
e documentado).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.data._comum import (
    COLUNAS_SAIDA,
    ArquivoExportacaoAusenteError,
    filtrar_data_corte,
)

FONTE = "ESTBAN/BCB (exportação manual)"
CAMINHO_PADRAO = Path("data/raw/estban/estban_municipios.csv")
VARIAVEIS_ESPERADAS = ("saldo_credito_pf", "saldo_poupanca")


def coletar(data_corte: dt.date, caminho: Path = CAMINHO_PADRAO) -> pd.DataFrame:
    """Lê a exportação manual normalizada do ESTBAN (ver docstring do módulo) —
    long-format já na origem, com `municipio_ibge` como unidade.

    Raises:
        ArquivoExportacaoAusenteError: se `caminho` não existir.
    """
    if not caminho.exists():
        raise ArquivoExportacaoAusenteError(
            f"exportação manual esperada em '{caminho}' não foi encontrada — "
            "ver docstring de src/data/estban.py para instruções de como obtê-la."
        )

    leitor = pd.read_excel if caminho.suffix.lower() in (".xlsx", ".xls") else pd.read_csv
    bruto = leitor(caminho)

    coletado_em = dt.datetime.now(dt.timezone.utc)
    df = pd.DataFrame(
        {
            "data_referencia": pd.to_datetime(bruto["data"]).dt.date,
            "unidade": bruto["municipio_ibge"].astype(str),
            "variavel": bruto["variavel"],
            "valor": pd.to_numeric(bruto["valor"], errors="coerce"),
            "fonte": FONTE,
            "coletado_em": coletado_em,
        }
    )[list(COLUNAS_SAIDA)]

    return filtrar_data_corte(df, data_corte)
