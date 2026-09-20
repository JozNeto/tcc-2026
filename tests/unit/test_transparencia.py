"""Testes unitários de src/data/transparencia.py — sem rede."""

from __future__ import annotations

import datetime as dt

import pytest
import requests

from src.data import transparencia

FIXTURE_MUNICIPIO_MES = [
    {"nis": "1", "valor": "600.00", "quantidadeBeneficiados": "3"},
    {"nis": "2", "valor": "300.00", "quantidadeBeneficiados": "1"},
]


class RespostaFake:
    def __init__(self, payload, status_ok: bool = True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("HTTP 500")

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def token_configurado(monkeypatch):
    monkeypatch.setenv(transparencia.TOKEN_ENV_VAR, "token-de-teste")


def test_token_ausente_levanta_erro_explicito(monkeypatch):
    monkeypatch.delenv(transparencia.TOKEN_ENV_VAR, raising=False)
    with pytest.raises(transparencia.ColetaTransparenciaError, match=transparencia.TOKEN_ENV_VAR):
        transparencia._token()


def test_somar_valor_e_beneficiarios():
    valor, quantidade = transparencia._somar_valor_e_beneficiarios(FIXTURE_MUNICIPIO_MES)
    assert valor == pytest.approx(900.0)
    assert quantidade == pytest.approx(4.0)


def test_somar_com_lista_vazia_retorna_zero():
    assert transparencia._somar_valor_e_beneficiarios([]) == (0.0, 0.0)


def test_coletar_monta_duas_variaveis_por_municipio_e_mes(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        assert headers == {"chave-api-dados": "token-de-teste"}
        return RespostaFake(FIXTURE_MUNICIPIO_MES)

    monkeypatch.setattr(transparencia.requests, "get", fake_get)

    resultado = transparencia.coletar(
        data_corte=dt.date(2026, 2, 28),
        codigos_ibge_municipio=["3550308"],
        data_inicial=dt.date(2026, 1, 1),
    )

    assert set(resultado["variavel"]) == {"bolsa_familia_valor_repassado", "bolsa_familia_beneficiarios"}
    assert set(resultado["unidade"]) == {"3550308"}
    # 2 meses (jan, fev) x 2 variáveis = 4 linhas
    assert len(resultado) == 4


def test_coletar_agrega_multiplos_municipios(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return RespostaFake(FIXTURE_MUNICIPIO_MES)

    monkeypatch.setattr(transparencia.requests, "get", fake_get)

    resultado = transparencia.coletar(
        data_corte=dt.date(2026, 1, 31),
        codigos_ibge_municipio=["3550308", "3304557"],
        data_inicial=dt.date(2026, 1, 1),
    )
    assert set(resultado["unidade"]) == {"3550308", "3304557"}


def test_requisitar_municipio_levanta_erro_explicito_em_falha_http(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return RespostaFake(None, status_ok=False)

    monkeypatch.setattr(transparencia.requests, "get", fake_get)

    with pytest.raises(transparencia.ColetaTransparenciaError, match="3550308"):
        transparencia._requisitar_municipio("3550308", "202601")
