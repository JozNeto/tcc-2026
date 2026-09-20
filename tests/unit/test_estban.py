import datetime as dt

import pandas as pd
import pytest

from src.data import estban
from src.data._comum import ArquivoExportacaoAusenteError


def test_coletar_levanta_erro_se_arquivo_ausente(tmp_path):
    with pytest.raises(ArquivoExportacaoAusenteError):
        estban.coletar(data_corte=dt.date(2025, 12, 31), caminho=tmp_path / "nao_existe.csv")


def test_coletar_le_arquivo_por_municipio(tmp_path):
    caminho = tmp_path / "estban.csv"
    pd.DataFrame(
        {
            "data": ["2025-01-01", "2025-01-01"],
            "municipio_ibge": ["3550308", "3550308"],
            "variavel": ["saldo_credito_pf", "saldo_poupanca"],
            "valor": [1_000_000.0, 500_000.0],
        }
    ).to_csv(caminho, index=False)

    df = estban.coletar(data_corte=dt.date(2025, 12, 31), caminho=caminho)

    assert set(df["variavel"]) == set(estban.VARIAVEIS_ESPERADAS)
    assert (df["unidade"] == "3550308").all()
