import datetime as dt

import pytest

from src.data import google_trends

CSV_REGIONAL = """Categoria: Todas as categorias

Região,apostas online: (01/01/2025 - 31/12/2025)
São Paulo,100
Rio de Janeiro,87
Bahia,76
"""

CSV_TEMPORAL = """Categoria: Todas as categorias

Semana,apostas online: (Brasil)
2025-01-05,45
2025-01-12,52
"""

CSV_INVALIDO = "coluna_a,coluna_b\n1,2\n"


def test_coletar_regional_parseia_uf_e_valor(tmp_path):
    caminho = tmp_path / "regional.csv"
    caminho.write_text(CSV_REGIONAL, encoding="utf-8")

    df = google_trends.coletar_regional(
        caminho, data_referencia=dt.date(2025, 12, 31), data_corte=dt.date(2025, 12, 31)
    )

    assert len(df) == 3
    assert set(df["unidade"]) == {"São Paulo", "Rio de Janeiro", "Bahia"}
    assert df.loc[df["unidade"] == "São Paulo", "valor"].iloc[0] == 100
    assert (df["variavel"] == google_trends.VARIAVEL).all()


def test_coletar_regional_rejeita_export_temporal(tmp_path):
    caminho = tmp_path / "temporal.csv"
    caminho.write_text(CSV_TEMPORAL, encoding="utf-8")

    with pytest.raises(google_trends.ExportacaoGoogleTrendsInvalidaError):
        google_trends.coletar_regional(
            caminho, data_referencia=dt.date(2025, 12, 31), data_corte=dt.date(2025, 12, 31)
        )


def test_coletar_temporal_parseia_datas_e_valores(tmp_path):
    caminho = tmp_path / "temporal.csv"
    caminho.write_text(CSV_TEMPORAL, encoding="utf-8")

    df = google_trends.coletar_temporal(caminho, unidade="BR", data_corte=dt.date(2025, 12, 31))

    assert len(df) == 2
    assert df["data_referencia"].iloc[0] == dt.date(2025, 1, 5)
    assert df["valor"].iloc[0] == 45
    assert (df["unidade"] == "BR").all()


def test_coletar_temporal_aplica_data_corte(tmp_path):
    csv_com_futuro = CSV_TEMPORAL + "2026-06-01,90\n"
    caminho = tmp_path / "temporal.csv"
    caminho.write_text(csv_com_futuro, encoding="utf-8")

    df = google_trends.coletar_temporal(caminho, unidade="BR", data_corte=dt.date(2025, 12, 31))

    assert df["data_referencia"].max() == dt.date(2025, 1, 12)


def test_cabecalho_ausente_levanta_erro(tmp_path):
    caminho = tmp_path / "invalido.csv"
    caminho.write_text(CSV_INVALIDO, encoding="utf-8")

    with pytest.raises(google_trends.ExportacaoGoogleTrendsInvalidaError):
        google_trends.coletar_temporal(caminho, unidade="BR", data_corte=dt.date(2025, 12, 31))
