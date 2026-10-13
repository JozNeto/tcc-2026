"""Testes unitários de src/data/sgs.py — sem rede.

As fixtures abaixo reproduzem o formato exato observado numa consulta real à API
(https://api.bcb.gov.br/dados/serie/bcdata.sgs.<codigo>/dados) em 2026-08-17.
"""

from __future__ import annotations

import datetime as dt

import pytest
import requests

from src.data import sgs

FIXTURE_29034 = [
    {"data": "01/02/2026", "valor": "28.30"},
    {"data": "01/03/2026", "valor": "28.21"},
    {"data": "01/04/2026", "valor": "28.36"},
    {"data": "01/05/2026", "valor": "28.48"},
]
FIXTURE_29037 = [
    {"data": "01/02/2026", "valor": "49.10"},
    {"data": "01/03/2026", "valor": "49.80"},
]
FIXTURE_21084 = [
    {"data": "01/02/2026", "valor": "5.56"},
    {"data": "01/03/2026", "valor": "5.40"},
]
FIXTURE_433 = [
    {"data": "01/03/2026", "valor": "0.21"},
    {"data": "01/05/2026", "valor": "0.58"},
    {"data": "01/06/2026", "valor": "0.16"},
    {"data": "01/07/2026", "valor": "0.07"},
]

FIXTURES_POR_CODIGO = {
    29034: FIXTURE_29034,
    29037: FIXTURE_29037,
    21084: FIXTURE_21084,
    433: FIXTURE_433,
}


class RespostaFake:
    def __init__(self, payload, status_ok: bool = True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("HTTP 500")

    def json(self):
        return self._payload


def test_parse_serie_converte_tipos_e_monta_colunas():
    coletado_em = dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc)
    df = sgs._parse_serie(FIXTURE_29034, "comprometimento_renda_pf", 29034, coletado_em)

    assert list(df.columns) == list(sgs.COLUNAS_SAIDA)
    assert len(df) == 4
    assert df["data_referencia"].iloc[0] == dt.date(2026, 2, 1)
    assert df["valor"].iloc[0] == pytest.approx(28.30)
    assert (df["unidade"] == "BR").all()
    assert (df["variavel"] == "comprometimento_renda_pf").all()
    assert df["fonte"].iloc[0] == "SGS/BCB (série 29034)"
    assert (df["coletado_em"] == coletado_em).all()


def test_parse_serie_aceita_decimal_com_virgula():
    coletado_em = dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc)
    dados = [{"data": "01/02/2026", "valor": "28,30"}]
    df = sgs._parse_serie(dados, "comprometimento_renda_pf", 29034, coletado_em)
    assert df["valor"].iloc[0] == pytest.approx(28.30)


def test_parse_serie_com_lista_vazia_retorna_dataframe_vazio_com_schema():
    coletado_em = dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc)
    df = sgs._parse_serie([], "comprometimento_renda_pf", 29034, coletado_em)
    assert df.empty
    assert list(df.columns) == list(sgs.COLUNAS_SAIDA)


def test_coletar_agrega_as_series_do_catalogo_padrao(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        codigo = int(url.split(".")[-1].split("/")[0])
        return RespostaFake(FIXTURES_POR_CODIGO[codigo])

    monkeypatch.setattr(sgs.requests, "get", fake_get)

    resultado = sgs.coletar(data_corte=dt.date(2026, 3, 31))

    assert set(resultado["variavel"]) == set(sgs.SERIES.keys())
    assert list(resultado.columns) == list(sgs.COLUNAS_SAIDA)
    # 4 + 2 + 2 linhas nas fixtures, mas 29034 tem uma linha de abril (posterior ao corte de março)
    assert resultado["data_referencia"].max() <= dt.date(2026, 3, 31)


def test_coletar_filtra_dados_posteriores_a_data_corte_defensivamente(monkeypatch):
    """Mesmo que a API (hipoteticamente) devolva algo além do dataFinal pedido, o
    cliente deve truncar de novo — o truncamento é uma garantia do
    cliente, não uma confiança cega na API."""

    def fake_get(url, params=None, timeout=None):
        return RespostaFake(FIXTURE_29034)  # inclui 01/05/2026

    monkeypatch.setattr(sgs.requests, "get", fake_get)

    resultado = sgs.coletar(data_corte=dt.date(2026, 3, 31), series={"comprometimento_renda_pf": 29034})

    assert resultado["data_referencia"].max() == dt.date(2026, 3, 1)


def test_coletar_passa_data_inicial_e_data_final_formatadas_em_pt_br(monkeypatch):
    chamadas = []

    def fake_get(url, params=None, timeout=None):
        chamadas.append(params)
        return RespostaFake(FIXTURE_29034)

    monkeypatch.setattr(sgs.requests, "get", fake_get)

    sgs.coletar(
        data_corte=dt.date(2025, 12, 31),
        data_inicial=dt.date(2020, 1, 1),
        series={"comprometimento_renda_pf": 29034},
    )

    assert chamadas[0]["dataInicial"] == "01/01/2020"
    assert chamadas[0]["dataFinal"] == "31/12/2025"


def test_requisitar_serie_levanta_erro_explicito_em_falha_http(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return RespostaFake(None, status_ok=False)

    monkeypatch.setattr(sgs.requests, "get", fake_get)

    with pytest.raises(sgs.ColetaSGSError, match="29034"):
        sgs._requisitar_serie(29034, None, dt.date(2025, 12, 31))


def test_requisitar_serie_levanta_erro_se_resposta_nao_for_lista(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return RespostaFake({"erro": "código inválido"})

    monkeypatch.setattr(sgs.requests, "get", fake_get)

    with pytest.raises(sgs.ColetaSGSError):
        sgs._requisitar_serie(999999, None, dt.date(2025, 12, 31))
