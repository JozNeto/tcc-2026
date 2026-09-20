
import pandas as pd
import pytest

from tests.data_quality.validadores import (
    COLUNAS_LONG_FORMAT,
    ValidacaoDadosError,
    combinar,
    validar_completude,
    validar_data_corte,
    validar_duplicatas,
    validar_range,
    validar_schema,
)


def test_validar_schema_aprova_quando_colunas_presentes(serie_long_exemplo):
    relatorio = validar_schema(serie_long_exemplo, COLUNAS_LONG_FORMAT)
    assert relatorio.aprovado


def test_validar_schema_reprova_quando_falta_coluna(serie_long_exemplo):
    df = serie_long_exemplo.drop(columns=["fonte"])
    relatorio = validar_schema(df, COLUNAS_LONG_FORMAT)
    assert not relatorio.aprovado
    assert "fonte" in relatorio.checagens_falhas[0]


def test_validar_duplicatas_aprova_sem_duplicata(serie_long_exemplo):
    relatorio = validar_duplicatas(serie_long_exemplo, ["data_referencia", "unidade", "variavel"])
    assert relatorio.aprovado


def test_validar_duplicatas_reprova_com_duplicata(serie_long_exemplo):
    df = pd.concat([serie_long_exemplo, serie_long_exemplo.iloc[[0]]], ignore_index=True)
    relatorio = validar_duplicatas(df, ["data_referencia", "unidade", "variavel"])
    assert not relatorio.aprovado


def test_validar_data_corte_aprova_dentro_do_corte(serie_long_exemplo, data_corte):
    relatorio = validar_data_corte(serie_long_exemplo, "data_referencia", data_corte)
    assert relatorio.aprovado


def test_validar_data_corte_reprova_dado_posterior(serie_long_exemplo, data_corte):
    df = serie_long_exemplo.copy()
    df.loc[len(df)] = df.iloc[-1]
    df.loc[df.index[-1], "data_referencia"] = pd.Timestamp("2026-06-01")
    relatorio = validar_data_corte(df, "data_referencia", data_corte)
    assert not relatorio.aprovado


def test_validar_data_corte_pode_ser_desativada_explicitamente(serie_long_exemplo, data_corte):
    df = serie_long_exemplo.copy()
    df.loc[len(df)] = df.iloc[-1]
    df.loc[df.index[-1], "data_referencia"] = pd.Timestamp("2026-06-01")
    relatorio = validar_data_corte(df, "data_referencia", data_corte, permitir_dados_pos_corte=True)
    assert relatorio.aprovado


def test_validar_completude_reprova_acima_do_limite():
    df = pd.DataFrame({"valor": [1.0, None, None, None]})
    relatorio = validar_completude(df, "valor", limite_ausencia=0.5)
    assert not relatorio.aprovado


def test_validar_completude_aprova_dentro_do_limite():
    df = pd.DataFrame({"valor": [1.0, 2.0, None, 4.0]})
    relatorio = validar_completude(df, "valor", limite_ausencia=0.5)
    assert relatorio.aprovado


def test_validar_range_reprova_valor_negativo_quando_nao_permitido():
    df = pd.DataFrame({"valor": [10.0, -5.0, 3.0]})
    relatorio = validar_range(df, "valor", minimo=0)
    assert not relatorio.aprovado


def test_combinar_agrega_falhas_de_multiplos_relatorios(serie_long_exemplo, data_corte):
    r1 = validar_schema(serie_long_exemplo.drop(columns=["fonte"]), COLUNAS_LONG_FORMAT)
    r2 = validar_data_corte(serie_long_exemplo, "data_referencia", data_corte)
    combinado = combinar(r1, r2)
    assert not combinado.aprovado
    assert len(combinado.checagens_falhas) == 1
    assert len(combinado.checagens_ok) == 1


def test_levantar_se_reprovado_levanta_com_detalhe(serie_long_exemplo):
    relatorio = validar_schema(serie_long_exemplo.drop(columns=["fonte"]), COLUNAS_LONG_FORMAT)
    with pytest.raises(ValidacaoDadosError, match="fonte"):
        relatorio.levantar_se_reprovado()
