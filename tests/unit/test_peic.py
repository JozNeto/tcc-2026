import datetime as dt

import pandas as pd
import pytest

from src.data import peic
from src.data._comum import ArquivoExportacaoAusenteError


def test_coletar_levanta_erro_se_arquivo_ausente(tmp_path):
    with pytest.raises(ArquivoExportacaoAusenteError):
        peic.coletar(data_corte=dt.date(2025, 12, 31), caminho=tmp_path / "nao_existe.csv")


def test_coletar_le_arquivo_normalizado(tmp_path):
    caminho = tmp_path / "peic.csv"
    pd.DataFrame({"data": ["2025-01-01", "2025-02-01"], "valor": [77.5, 78.1]}).to_csv(caminho, index=False)

    df = peic.coletar(data_corte=dt.date(2025, 12, 31), caminho=caminho)

    assert len(df) == 2
    assert (df["variavel"] == peic.VARIAVEL).all()
    assert (df["unidade"] == "BR").all()
