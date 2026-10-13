from __future__ import annotations

import pandas as pd
import pytest

from src.data import transparencia_fatias as tf

MUNICIPIOS = pd.DataFrame(
    {"codigo_ibge": ["1", "2", "3", "4"], "uf": ["SP", "SP", "RJ", "RJ"]}
)


def _consulta_ok(codigo, mes):
    return [{"valor": 100.0, "quantidadeBeneficiados": 10}]


def test_respeita_tamanho_da_fatia(tmp_path):
    arq = tmp_path / "p.csv"
    r = tf.coletar_fatia(MUNICIPIOS, "202512", arq, tamanho_fatia=2, consultar=_consulta_ok, dormir=lambda s: None)
    assert r["coletados_nesta_execucao"] == 2
    assert len(tf.ler_progresso(arq)) == 2


def test_retoma_sem_repetir_municipios(tmp_path):
    arq = tmp_path / "p.csv"
    chamadas = []

    def consulta(codigo, mes):
        chamadas.append(codigo)
        return _consulta_ok(codigo, mes)

    tf.coletar_fatia(MUNICIPIOS, "202512", arq, tamanho_fatia=2, consultar=consulta, dormir=lambda s: None)
    tf.coletar_fatia(MUNICIPIOS, "202512", arq, tamanho_fatia=10, consultar=consulta, dormir=lambda s: None)
    assert chamadas == ["1", "2", "3", "4"]


def test_para_no_limite_de_uso_e_preserva_progresso(tmp_path):
    arq = tmp_path / "p.csv"

    def consulta(codigo, mes):
        if codigo == "3":
            raise tf.LimiteDeUsoError("429")
        return _consulta_ok(codigo, mes)

    r = tf.coletar_fatia(MUNICIPIOS, "202512", arq, tamanho_fatia=10, consultar=consulta, dormir=lambda s: None)
    assert r["parou_por_limite"] is True
    assert list(tf.ler_progresso(arq)["codigo_ibge"]) == ["1", "2"]


def test_municipio_sem_registro_nao_vira_zero(tmp_path):
    arq = tmp_path / "p.csv"
    tf.coletar_fatia(MUNICIPIOS.head(1), "202512", arq, consultar=lambda c, m: [], dormir=lambda s: None)
    linha = tf.ler_progresso(arq).iloc[0]
    assert linha["status"] == "sem_registro"
    assert pd.isna(linha["valor"])


def test_pausa_entre_chamadas(tmp_path):
    pausas = []
    tf.coletar_fatia(
        MUNICIPIOS, "202512", tmp_path / "p.csv", tamanho_fatia=3, pausa_segundos=1.5,
        consultar=_consulta_ok, dormir=pausas.append,
    )
    assert pausas == [1.5, 1.5, 1.5]


def test_agregar_por_uf_informa_cobertura(tmp_path):
    arq = tmp_path / "p.csv"
    tf.coletar_fatia(MUNICIPIOS, "202512", arq, tamanho_fatia=3, consultar=_consulta_ok, dormir=lambda s: None)
    agg = tf.agregar_por_uf(arq).set_index("uf")
    assert agg.loc["SP", "valor_repassado"] == 200.0
    assert agg.loc["RJ", "municipios_coletados"] == 1


def test_consultar_municipio_levanta_limite_em_429(monkeypatch):
    monkeypatch.setenv(tf.TOKEN_ENV_VAR, "x")

    class R:
        status_code = 429

    monkeypatch.setattr(tf.requests, "get", lambda *a, **k: R())
    with pytest.raises(tf.LimiteDeUsoError):
        tf.consultar_municipio("1", "202512")
