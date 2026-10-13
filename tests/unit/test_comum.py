import datetime as dt

import pandas as pd
import pytest

from src.data._comum import (
    COLUNAS_SAIDA,
    ArquivoExportacaoAusenteError,
    filtrar_data_corte,
    ler_planilha_exportada,
    montar_long,
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
