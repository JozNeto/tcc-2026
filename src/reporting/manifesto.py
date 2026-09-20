"""Rastreamento de proveniência das figuras publicadas (spec 05, critério 2):
toda figura em `reports/final/figuras/` tem script gerador, versão da base usada e
data de geração registrados em `reports/final/figuras/manifesto.csv`.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

COLUNAS_MANIFESTO = ("nome_figura", "script_gerador", "versao_base_usada", "data_geracao")


def registrar_proveniencia(
    caminho_manifesto: Path,
    nome_figura: str,
    script_gerador: str,
    versao_base_usada: str,
    data_geracao: dt.datetime | None = None,
) -> None:
    """Acrescenta uma linha ao manifesto CSV de proveniência (cria o arquivo e o
    cabeçalho na primeira chamada)."""
    linha = pd.DataFrame(
        [
            {
                "nome_figura": nome_figura,
                "script_gerador": script_gerador,
                "versao_base_usada": versao_base_usada,
                "data_geracao": (data_geracao or dt.datetime.now(dt.timezone.utc)).isoformat(),
            }
        ]
    )[list(COLUNAS_MANIFESTO)]

    caminho_manifesto.parent.mkdir(parents=True, exist_ok=True)
    escrever_cabecalho = not caminho_manifesto.exists()
    linha.to_csv(caminho_manifesto, mode="a", header=escrever_cabecalho, index=False)


def ler_manifesto(caminho_manifesto: Path) -> pd.DataFrame:
    if not caminho_manifesto.exists():
        return pd.DataFrame(columns=list(COLUNAS_MANIFESTO))
    return pd.read_csv(caminho_manifesto)
