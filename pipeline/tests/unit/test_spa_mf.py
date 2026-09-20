import datetime as dt

import pandas as pd
import pytest

from src.data import spa_mf
from src.data._comum import ArquivoExportacaoAusenteError


def test_coletar_levanta_erro_se_arquivo_ausente(tmp_path):
    with pytest.raises(ArquivoExportacaoAusenteError):
        spa_mf.coletar(data_corte=dt.date(2025, 12, 31), caminho=tmp_path / "nao_existe.csv")


def test_coletar_le_arquivo_long_format_com_3_variaveis(tmp_path):
    caminho = tmp_path / "spa_mf.csv"
    pd.DataFrame(
        {
            "data": ["2025-01-01", "2025-01-01", "2025-01-01"],
            "variavel": ["apostadores_qtd", "ggr_valor", "ticket_medio_valor"],
            "valor": [17_700_000, 17_400_000_000, 164.0],
        }
    ).to_csv(caminho, index=False)

    df = spa_mf.coletar(data_corte=dt.date(2025, 12, 31), caminho=caminho)

    assert set(df["variavel"]) == set(spa_mf.VARIAVEIS_ESPERADAS)
    assert len(df) == 3


def test_coletar_aplica_data_corte(tmp_path):
    caminho = tmp_path / "spa_mf.csv"
    pd.DataFrame(
        {"data": ["2025-01-01", "2026-01-01"], "variavel": ["apostadores_qtd", "apostadores_qtd"], "valor": [1, 2]}
    ).to_csv(caminho, index=False)

    df = spa_mf.coletar(data_corte=dt.date(2025, 12, 31), caminho=caminho)

    assert len(df) == 1
    assert df["data_referencia"].iloc[0] == dt.date(2025, 1, 1)
