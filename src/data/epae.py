"""Ingestão da EPAE/BCB — Estatísticas de Pagamentos por Atividade Econômica
: fluxo de Pix de pessoas físicas para o setor de recreação,
usado como proxy de exposição agregada a apostas online.

**Sem dataset aberto/API confirmada.** A EPAE é uma estatística nova (BCB começou a
divulgá-la em out/2025); a verificação em 2026-08-17 não encontrou dataset no
Portal de Dados Abertos do BCB nem endpoint OData estável — apenas divulgação em
caixas de texto do Relatório de Política Monetária (PDF). Conforme
a política do projeto de evitar scraping, este módulo não faz scraping de PDF: espera um arquivo
normalizado, exportado/transcrito manualmente a partir da divulgação oficial do BCB,
em `data/raw/epae/`.

Formato esperado do arquivo normalizado (CSV ou XLSX), colunas:
    data    : data de referência do mês
    valor   : valor de Pix de pessoas físicas para o setor "recreação" (CNAE), em R$

Antes de uma nova rodada de coleta, reconfirmar em https://dadosabertos.bcb.gov.br/
se a EPAE já tem dataset/API própria — se sim, este módulo deve ser reescrito para
consumi-la diretamente.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.data._comum import ler_planilha_exportada

FONTE = "EPAE/BCB (exportação manual)"
CAMINHO_PADRAO = Path("data/raw/epae/epae_pix_recreacao.csv")
VARIAVEL = "pix_pf_setor_recreacao_valor"


def coletar(data_corte: dt.date, caminho: Path = CAMINHO_PADRAO) -> pd.DataFrame:
    """Lê a exportação manual normalizada da EPAE (ver docstring do módulo).

    Raises:
        ArquivoExportacaoAusenteError: se `caminho` não existir.
    """
    return ler_planilha_exportada(
        caminho=caminho,
        coluna_data_origem="data",
        coluna_valor_origem="valor",
        variavel=VARIAVEL,
        unidade="BR",
        fonte=FONTE,
        data_corte=data_corte,
    )
