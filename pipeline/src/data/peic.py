"""Ingestão da PEIC/CNC — Pesquisa de Endividamento e Inadimplência do Consumidor
.

**Sem API oficial nem exportação pública direta confirmada.** A verificação feita em
2026-08-17 mostrou que
os microdados/série histórica da PEIC ficam atrás de área logada em
pesquisascnc.com.br — os releases públicos são PDFs mensais, não uma série tabular
baixável. Conforme a política do projeto (evitar scraping ao máximo), este módulo
**não faz scraping de PDF/HTML**: espera um arquivo normalizado, exportado
manualmente por um integrante do grupo com acesso à área logada (ou transcrito dos
releases em PDF), e colocado em `data/raw/peic/`.

Formato esperado do arquivo normalizado (CSV ou XLSX), colunas:
    data    : data de referência do mês (qualquer formato reconhecido pelo pandas)
    valor   : percentual de famílias endividadas (indicador principal da PEIC)

Se a PEIC vier a publicar uma API ou exportação tabular oficial no futuro, este
módulo deve ser reescrito para consumi-la diretamente.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.data._comum import ler_planilha_exportada

FONTE = "PEIC/CNC (exportação manual)"
CAMINHO_PADRAO = Path("data/raw/peic/peic_familias_endividadas.csv")
VARIAVEL = "percentual_familias_endividadas"


def coletar(data_corte: dt.date, caminho: Path = CAMINHO_PADRAO) -> pd.DataFrame:
    """Lê a exportação manual normalizada da PEIC (ver docstring do módulo).

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
