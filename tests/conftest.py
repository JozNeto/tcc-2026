"""Fixtures compartilhadas do harness de testes.

Mantém o harness independente de dados reais: qualquer fixture que precise de um
DataFrame de exemplo gera dados sintéticos aqui, nunca lê data/raw/ (git-ignored e
não determinístico entre máquinas).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

DATA_CORTE_PROJETO = date(2025, 12, 31)


@pytest.fixture
def data_corte() -> date:
    """Data de corte fixa do projeto (specs/constitution.md §3)."""
    return DATA_CORTE_PROJETO


@pytest.fixture
def serie_long_exemplo() -> pd.DataFrame:
    """DataFrame sintético no contrato long-format de specs/01-ingestao-dados/spec.md."""
    datas = pd.date_range("2020-01-01", "2025-12-01", freq="MS")
    return pd.DataFrame(
        {
            "data_referencia": datas,
            "unidade": "BR",
            "variavel": "comprometimento_renda_pf",
            "valor": range(len(datas)),
            "fonte": "SGS/BCB",
            "coletado_em": pd.Timestamp("2026-01-15"),
        }
    )
