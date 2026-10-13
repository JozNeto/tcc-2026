"""Teste de integração real de src/data/sgs.py contra a API do BCB.

Roda via `make test-network` (não em `make test` padrão)
critério 1 exige um teste de integração de rede separado do teste unitário com fixture.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.data import sgs

pytestmark = pytest.mark.network


def test_coletar_retorna_dados_reais_para_todas_as_series():
    resultado = sgs.coletar(data_corte=dt.datetime.now(dt.timezone.utc).date())

    assert not resultado.empty
    assert set(resultado["variavel"]) == set(sgs.SERIES.keys())

    # Séries de percentual "de nível" (comprometimento, endividamento, inadimplência)
    # variam tipicamente entre 0 e 100. IPCA (série 433) tem histórico completo desde
    # a hiperinflação brasileira (variações mensais de dezenas de %) — checar só que
    # os valores mais recentes (12 últimos meses) estão numa faixa plausível.
    series_percentual_nivel = resultado[resultado["variavel"] != "ipca_variacao_mensal"]
    ipca_recente = resultado[resultado["variavel"] == "ipca_variacao_mensal"].sort_values("data_referencia").tail(12)

    assert series_percentual_nivel["valor"].between(0, 100).all()
    assert not ipca_recente.empty
    assert ipca_recente["valor"].between(-5, 5).all()
