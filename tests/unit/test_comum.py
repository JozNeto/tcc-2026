import datetime as dt

import pandas as pd
import pytest
import requests

from src.data import _comum
from src.data._comum import (
    COLUNAS_SAIDA,
    ArquivoExportacaoAusenteError,
    filtrar_data_corte,
    ler_planilha_exportada,
    montar_long,
    requisitar_com_retentativas,
)


def test_montar_long_produz_schema_esperado():
    coletado_em = dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc)
    df = montar_long(
        datas=[dt.date(2025, 1, 1), dt.date(2025, 2, 1)],
        valores=[1.0, 2.0],
        variavel="x",
        unidade="BR",
        fonte="teste",
        coletado_em=coletado_em,
    )
    assert list(df.columns) == list(COLUNAS_SAIDA)
    assert len(df) == 2


def test_filtrar_data_corte_remove_linhas_posteriores():
    df = montar_long(
        datas=[dt.date(2025, 1, 1), dt.date(2026, 1, 1)],
        valores=[1.0, 2.0],
        variavel="x",
        unidade="BR",
        fonte="teste",
        coletado_em=dt.datetime.now(dt.timezone.utc),
    )
    filtrado = filtrar_data_corte(df, dt.date(2025, 12, 31))
    assert len(filtrado) == 1
    assert filtrado["data_referencia"].iloc[0] == dt.date(2025, 1, 1)


def test_filtrar_data_corte_com_df_vazio_nao_quebra():
    df = pd.DataFrame(columns=list(COLUNAS_SAIDA))
    assert filtrar_data_corte(df, dt.date(2025, 12, 31)).empty


def test_ler_planilha_exportada_levanta_erro_se_arquivo_ausente(tmp_path):
    with pytest.raises(ArquivoExportacaoAusenteError, match="não foi encontrada"):
        ler_planilha_exportada(
            caminho=tmp_path / "nao_existe.csv",
            coluna_data_origem="data",
            coluna_valor_origem="valor",
            variavel="x",
            unidade="BR",
            fonte="teste",
            data_corte=dt.date(2025, 12, 31),
        )


def test_ler_planilha_exportada_le_csv_e_aplica_data_corte(tmp_path):
    caminho = tmp_path / "exportacao.csv"
    pd.DataFrame({"data": ["2025-01-01", "2026-03-01"], "valor": [10, 20]}).to_csv(caminho, index=False)

    df = ler_planilha_exportada(
        caminho=caminho,
        coluna_data_origem="data",
        coluna_valor_origem="valor",
        variavel="minha_variavel",
        unidade="BR",
        fonte="teste",
        data_corte=dt.date(2025, 12, 31),
    )

    assert len(df) == 1
    assert df["variavel"].iloc[0] == "minha_variavel"
    assert df["valor"].iloc[0] == 10.0


def test_ler_planilha_exportada_usa_coluna_de_unidade_quando_informada(tmp_path):
    caminho = tmp_path / "exportacao.csv"
    pd.DataFrame(
        {"data": ["2025-01-01", "2025-01-01"], "uf": ["SP", "RJ"], "valor": [1, 2]}
    ).to_csv(caminho, index=False)

    df = ler_planilha_exportada(
        caminho=caminho,
        coluna_data_origem="data",
        coluna_valor_origem="valor",
        variavel="x",
        unidade="BR",  # ignorado, pois unidade_coluna_origem tem prioridade
        fonte="teste",
        data_corte=dt.date(2025, 12, 31),
        unidade_coluna_origem="uf",
    )

    assert set(df["unidade"]) == {"SP", "RJ"}


class _RespostaFake:
    def __init__(self, status_code: int):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


def test_requisitar_com_retentativas_sucesso_de_primeira(monkeypatch):
    chamadas = []
    monkeypatch.setattr(_comum.requests, "get", lambda *a, **k: chamadas.append(1) or _RespostaFake(200))

    resposta = requisitar_com_retentativas("http://x", dormir=lambda s: pytest.fail("não deveria dormir"))

    assert resposta.status_code == 200
    assert len(chamadas) == 1


def test_requisitar_com_retentativas_insiste_em_erro_5xx_e_depois_funciona(monkeypatch):
    respostas = iter([_RespostaFake(502), _RespostaFake(502), _RespostaFake(200)])
    monkeypatch.setattr(_comum.requests, "get", lambda *a, **k: next(respostas))
    esperas = []

    resposta = requisitar_com_retentativas("http://x", tentativas=4, dormir=esperas.append)

    assert resposta.status_code == 200
    assert len(esperas) == 2  # duas falhas antes do sucesso


def test_requisitar_com_retentativas_nao_insiste_em_erro_4xx(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        _comum.requests, "get", lambda *a, **k: chamadas.append(1) or _RespostaFake(404)
    )

    with pytest.raises(requests.HTTPError):
        requisitar_com_retentativas("http://x", dormir=lambda s: pytest.fail("não deveria dormir"))

    assert len(chamadas) == 1  # não retentou


def test_requisitar_com_retentativas_desiste_apos_esgotar_tentativas(monkeypatch):
    monkeypatch.setattr(_comum.requests, "get", lambda *a, **k: _RespostaFake(503))
    esperas = []

    with pytest.raises(requests.HTTPError):
        requisitar_com_retentativas("http://x", tentativas=3, dormir=esperas.append)

    assert len(esperas) == 2  # dorme entre tentativas, não após a última


def test_requisitar_com_retentativas_insiste_em_erro_de_conexao(monkeypatch):
    chamadas = {"n": 0}

    def fake_get(*a, **k):
        chamadas["n"] += 1
        if chamadas["n"] < 2:
            raise requests.ConnectionError("conexão recusada")
        return _RespostaFake(200)

    monkeypatch.setattr(_comum.requests, "get", fake_get)
    esperas = []

    resposta = requisitar_com_retentativas("http://x", dormir=esperas.append)

    assert resposta.status_code == 200
    assert len(esperas) == 1
