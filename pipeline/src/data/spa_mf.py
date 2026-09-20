"""Ingestão dos painéis semestrais da SPA/MF — Secretaria de Prêmios e Apostas do
Ministério da Fazenda (spec 01, camada Núcleo): número de apostadores, GGR, tíquete
médio e perfil demográfico.

**Sem API pública.** Os painéis da SPA/MF são publicados como relatórios/painéis
semestrais (PDF e, em alguns casos, painel interativo tipo Power BI) sem endpoint de
dados aberto confirmado. Conforme specs/constitution.md §4, este módulo não faz
scraping do painel interativo nem de PDF: espera um arquivo normalizado, exportado
manualmente (via o botão de exportação do próprio painel, quando disponível, ou
transcrito do relatório oficial em PDF) e colocado em `data/raw/spa_mf/`.

Formato esperado do arquivo normalizado (CSV ou XLSX), colunas:
    data      : data de referência do semestre (usar o 1º dia do semestre, ex.:
                2025-01-01 para o 1º semestre de 2025)
    variavel  : um de {"apostadores_qtd", "ggr_valor", "ticket_medio_valor"}
    valor     : valor numérico correspondente

Como a divulgação é semestral, cada linha representa um semestre inteiro — a
harmonização de periodicidade com as séries mensais do núcleo nacional é
responsabilidade de `src/features/tratamento.py` (spec 02), não deste módulo.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.data._comum import COLUNAS_SAIDA, filtrar_data_corte

FONTE = "SPA/MF (exportação manual, painel semestral)"
CAMINHO_PADRAO = Path("data/raw/spa_mf/spa_mf_paineis.csv")
VARIAVEIS_ESPERADAS = ("apostadores_qtd", "ggr_valor", "ticket_medio_valor")


def coletar(data_corte: dt.date, caminho: Path = CAMINHO_PADRAO) -> pd.DataFrame:
    """Lê a exportação manual normalizada dos painéis SPA/MF (ver docstring do
    módulo) — formato long-format já na origem (`variavel` é uma coluna do arquivo,
    diferente de `peic.py`/`epae.py`, pois este arquivo cobre 3 variáveis).

    Raises:
        FileNotFoundError: se `caminho` não existir (checagem própria, não via
            `_comum.ler_planilha_exportada`, pois o arquivo aqui já vem long-format).
    """
    if not caminho.exists():
        from src.data._comum import ArquivoExportacaoAusenteError

        raise ArquivoExportacaoAusenteError(
            f"exportação manual esperada em '{caminho}' não foi encontrada — "
            "ver docstring de src/data/spa_mf.py para instruções de como obtê-la."
        )

    leitor = pd.read_excel if caminho.suffix.lower() in (".xlsx", ".xls") else pd.read_csv
    bruto = leitor(caminho)

    coletado_em = dt.datetime.now(dt.timezone.utc)
    df = pd.DataFrame(
        {
            "data_referencia": pd.to_datetime(bruto["data"]).dt.date,
            "unidade": "BR",
            "variavel": bruto["variavel"],
            "valor": pd.to_numeric(bruto["valor"], errors="coerce"),
            "fonte": FONTE,
            "coletado_em": coletado_em,
        }
    )[list(COLUNAS_SAIDA)]

    return filtrar_data_corte(df, data_corte)
