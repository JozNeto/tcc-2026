from __future__ import annotations

import pytest
import requests

from src.data import ibge_uf


class Resp:
    def __init__(self, dados, ok=True):
        self._d, self._ok = dados, ok

    def raise_for_status(self):
        if not self._ok:
            raise requests.HTTPError("400")

    def json(self):
        return self._d


def _dados(qtd=27):
    cab = {"D1C": "Unidade da Federação (Código)"}
    linhas = [{"D1C": str(cod), "D3C": "2025", "V": "100"} for cod in list(ibge_uf.COD_UF)[:qtd]]
    return [cab, *linhas]


def test_devolve_27_ufs_com_sigla(monkeypatch):
    monkeypatch.setattr(ibge_uf.requests, "get", lambda *a, **k: Resp(_dados()))
    df = ibge_uf.coletar_por_uf(6579, 9324, "2025")
    assert df["uf"].nunique() == 27
    assert set(df["uf"]) == set(ibge_uf.COD_UF.values())


def test_erro_se_faltar_uf(monkeypatch):
    monkeypatch.setattr(ibge_uf.requests, "get", lambda *a, **k: Resp(_dados(26)))
    with pytest.raises(ibge_uf.IbgeUfError):
        ibge_uf.coletar_por_uf(6579, 9324, "2025")


def test_erro_explicito_em_falha_http(monkeypatch):
    monkeypatch.setattr(ibge_uf.requests, "get", lambda *a, **k: Resp(None, ok=False))
    with pytest.raises(ibge_uf.IbgeUfError):
        ibge_uf.coletar_por_uf(6390, 5933, "202512")
