from __future__ import annotations

import datetime as dt

import pandas as pd

from src.reporting.figuras import plotar_cenarios, plotar_serie_com_intervalo
from src.reporting.manifesto import ler_manifesto, registrar_proveniencia


def _previsao() -> pd.DataFrame:
    datas = pd.date_range("2026-01-01", periods=6, freq="MS").date
    return pd.DataFrame(
        {
            "data_referencia": datas,
            "previsao": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            "intervalo_inferior": [8.0, 9.0, 10.0, 11.0, 12.0, 13.0],
            "intervalo_superior": [12.0, 13.0, 14.0, 15.0, 16.0, 17.0],
        }
    )


def test_plotar_serie_com_intervalo_salva_arquivo(tmp_path):
    caminho = tmp_path / "figura.png"
    fig = plotar_serie_com_intervalo(_previsao(), titulo="teste", caminho_saida=caminho)

    assert caminho.exists()
    assert caminho.stat().st_size > 0
    import matplotlib.pyplot as plt

    plt.close(fig)


def test_plotar_serie_com_intervalo_aceita_historico(tmp_path):
    historico = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2025-10-01", periods=3, freq="MS").date)
    caminho = tmp_path / "figura.png"
    fig = plotar_serie_com_intervalo(_previsao(), serie_historica=historico, caminho_saida=caminho)

    assert caminho.exists()
    import matplotlib.pyplot as plt

    plt.close(fig)


def test_plotar_cenarios_salva_arquivo(tmp_path):
    previsao = _previsao()
    cenarios = pd.concat(
        [previsao.assign(cenario=c) for c in ("inercial", "contencao", "expansao")], ignore_index=True
    )
    caminho = tmp_path / "cenarios.png"
    fig = plotar_cenarios(cenarios, titulo="teste", caminho_saida=caminho)

    assert caminho.exists()
    import matplotlib.pyplot as plt

    plt.close(fig)


def test_registrar_proveniencia_cria_arquivo_com_cabecalho(tmp_path):
    caminho = tmp_path / "manifesto.csv"
    registrar_proveniencia(
        caminho,
        nome_figura="fig1.png",
        script_gerador="src/reporting/figuras.py",
        versao_base_usada="base_nacional_corte-2025-12-31_run-teste",
        data_geracao=dt.datetime(2026, 8, 17, tzinfo=dt.timezone.utc),
    )

    manifesto = ler_manifesto(caminho)
    assert len(manifesto) == 1
    assert manifesto.iloc[0]["nome_figura"] == "fig1.png"


def test_registrar_proveniencia_acrescenta_sem_duplicar_cabecalho(tmp_path):
    caminho = tmp_path / "manifesto.csv"
    for i in range(3):
        registrar_proveniencia(caminho, f"fig{i}.png", "script.py", "versao-teste")

    manifesto = ler_manifesto(caminho)
    assert len(manifesto) == 3
    assert list(manifesto.columns) == ["nome_figura", "script_gerador", "versao_base_usada", "data_geracao"]


def test_ler_manifesto_inexistente_retorna_vazio(tmp_path):
    resultado = ler_manifesto(tmp_path / "nao_existe.csv")
    assert resultado.empty
