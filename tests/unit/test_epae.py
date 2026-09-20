import datetime as dt

import pandas as pd
import pytest

from src.data import epae
from src.data._comum import ArquivoExportacaoAusenteError


def test_coletar_levanta_erro_se_arquivo_ausente(tmp_path):
    with pytest.raises(ArquivoExportacaoAusenteError):
        epae.coletar(data_corte=dt.date(2025, 12, 31), caminho=tmp_path / "nao_existe.csv")


def test_coletar_le_arquivo_normalizado(tmp_path):
    caminho = tmp_path / "epae.csv"
    pd.DataFrame({"data": ["2025-01-01"], "valor": [1_500_000.0]}).to_csv(caminho, index=False)

    df = epae.coletar(data_corte=dt.date(2025, 12, 31), caminho=caminho)

    assert len(df) == 1
    assert df["variavel"].iloc[0] == epae.VARIAVEL
