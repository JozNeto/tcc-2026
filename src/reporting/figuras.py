"""Geração de figuras para a monografia.

Este módulo só formata/plota o que já foi calculado em `src/features/` e
`src/models/` — nenhuma lógica de cálculo nova aqui.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem display — necessário para rodar em CI/servidor
import matplotlib.pyplot as plt
import pandas as pd


def plotar_serie_com_intervalo(
    previsao: pd.DataFrame,
    serie_historica: pd.Series | None = None,
    titulo: str = "",
    caminho_saida: Path | None = None,
) -> plt.Figure:
    """Plota uma previsão (`data_referencia`, `previsao`, `intervalo_inferior`,
    `intervalo_superior` — contrato de `src/models/base.py`) sobre o histórico,
    quando informado."""
    fig, eixo = plt.subplots(figsize=(10, 5))

    if serie_historica is not None:
        eixo.plot(serie_historica.index, serie_historica.to_numpy(), label="Histórico", color="tab:gray")

    eixo.plot(previsao["data_referencia"], previsao["previsao"], label="Previsão", color="tab:blue")
    eixo.fill_between(
        previsao["data_referencia"],
        previsao["intervalo_inferior"],
        previsao["intervalo_superior"],
        alpha=0.2,
        color="tab:blue",
        label="Intervalo de predição (95%)",
    )

    eixo.set_title(titulo)
    eixo.legend()
    fig.autofmt_xdate()

    if caminho_saida is not None:
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(caminho_saida, bbox_inches="tight")

    return fig


def plotar_cenarios(cenarios: pd.DataFrame, titulo: str = "", caminho_saida: Path | None = None) -> plt.Figure:
    """Plota os três cenários (`inercial`, `contencao`, `expansao` — saída de
    `src/models/cenarios.py`) numa única figura comparativa."""
    fig, eixo = plt.subplots(figsize=(10, 5))

    for nome_cenario, grupo in cenarios.groupby("cenario"):
        eixo.plot(grupo["data_referencia"], grupo["previsao"], label=nome_cenario)
        eixo.fill_between(grupo["data_referencia"], grupo["intervalo_inferior"], grupo["intervalo_superior"], alpha=0.1)

    eixo.set_title(titulo)
    eixo.legend()
    fig.autofmt_xdate()

    if caminho_saida is not None:
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(caminho_saida, bbox_inches="tight")

    return fig
