"""Teste de integração real de src/data/ibge.py contra a API SIDRA.

Roda via `make test-network`.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.data import ibge

pytestmark = pytest.mark.network


def test_coletar_retorna_dados_reais_para_todas_as_tabelas():
    resultado = ibge.coletar(data_corte=dt.datetime.now(dt.timezone.utc).date())

    assert not resultado.empty
    assert set(resultado["variavel"]) == set(ibge.TABELAS.keys())
