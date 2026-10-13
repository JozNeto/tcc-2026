"""Testes unitários de src/data/ibge.py — sem rede.

As fixtures reproduzem o formato exato observado em consultas reais à API SIDRA
(https://apisidra.ibge.gov.br/values/...) em 2026-08-17.
"""

from __future__ import annotations

import datetime as dt

import pytest
import requests

from src.data import ibge

CABECALHO = {
    "NC": "Nível Territorial (Código)",
    "NN": "Nível Territorial",
    "MC": "Unidade de Medida (Código)",
    "MN": "Unidade de Medida",
    "V": "Valor",
    "D1C": "Brasil (Código)",
    "D1N": "Brasil",
    "D2C": "Variável (Código)",
    "D2N": "Variável",
    "D3C": "Período (Código)",
    "D3N": "Período",
}

FIXTURE_TAXA_DESOCUPACAO = [
    CABECALHO,
    {"NC": "1", "NN": "Brasil", "V": "5.4", "D1C": "1", "D2C": "4099", "D3C": "202606", "D3N": "abr-mai-jun 2026"},
    {"NC": "1", "NN": "Brasil", "V": "5.2", "D1C": "1", "D2C": "4099", "D3C": "202605", "D3N": "mar-abr-mai 2026"},
]

FIXTURE_POPULACAO = [
    CABECALHO,
    {"NC": "1", "NN": "Brasil", "V": "213421037", "D1C": "1", "D2C": "9324", "D3C": "2025", "D3N": "2025"},
]

FIXTURE_POR_TABELA = {6381: FIXTURE_TAXA_DESOCUPACAO, 6579: FIXTURE_POPULACAO}


class RespostaFake:
    def __init__(self, payload, status_ok: bool = True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("HTTP 500")

    def json(self):
        return self._payload


def test_parse_periodo_mensal():
    assert ibge._parse_periodo("202606") == dt.date(2026, 6, 1)


def test_parse_periodo_anual_usa_1_de_julho():
    assert ibge._parse_periodo("2025") == dt.date(2025, 7, 1)


def test_parse_periodo_formato_invalido_levanta_erro():
    with pytest.raises(ibge.ColetaIBGEError):
        ibge._parse_periodo("26")


def test_parse_tabela_monta_schema_esperado():
    coletado_em = dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc)
    df = ibge._parse_tabela(
        FIXTURE_TAXA_DESOCUPACAO[1:], "taxa_desocupacao", ibge.TABELAS["taxa_desocupacao"], coletado_em
    )
    assert list(df.columns) == list(ibge.COLUNAS_SAIDA)
    assert len(df) == 2
    assert df["valor"].iloc[0] == pytest.approx(5.4)
    assert df["data_referencia"].iloc[0] == dt.date(2026, 6, 1)


def test_coletar_agrega_series_do_catalogo_padrao(monkeypatch):
    def fake_get(url, timeout=None):
        codigo = int(url.split("/t/")[1].split("/")[0])
        return RespostaFake(FIXTURE_POR_TABELA[codigo])

    monkeypatch.setattr(ibge.requests, "get", fake_get)

    tabelas = {"taxa_desocupacao": ibge.TABELAS["taxa_desocupacao"], "populacao_estimada": ibge.TABELAS["populacao_estimada"]}
    resultado = ibge.coletar(data_corte=dt.date(2026, 6, 30), tabelas=tabelas)

    assert set(resultado["variavel"]) == {"taxa_desocupacao", "populacao_estimada"}


def test_coletar_filtra_por_data_corte(monkeypatch):
    def fake_get(url, timeout=None):
        return RespostaFake(FIXTURE_TAXA_DESOCUPACAO)

    monkeypatch.setattr(ibge.requests, "get", fake_get)

    resultado = ibge.coletar(
        data_corte=dt.date(2026, 5, 31), tabelas={"taxa_desocupacao": ibge.TABELAS["taxa_desocupacao"]}
    )
    assert resultado["data_referencia"].max() == dt.date(2026, 5, 1)


def test_requisitar_tabela_levanta_erro_explicito_em_falha_http(monkeypatch):
    def fake_get(url, timeout=None):
        return RespostaFake(None, status_ok=False)

    monkeypatch.setattr(ibge.requests, "get", fake_get)

    with pytest.raises(ibge.ColetaIBGEError, match="taxa_desocupacao"):
        ibge._requisitar_tabela("taxa_desocupacao", ibge.TABELAS["taxa_desocupacao"])
