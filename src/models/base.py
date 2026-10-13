"""Interface comum da escada de modelos.

Todo modelo em `src/models/` implementa `ModeloSerie` — isso é o que permite que
`src/models/validacao.py` (rolling origin) e `src/evaluation/` comparem qualquer
modelo da escada de forma intercambiável, sem conhecer os detalhes de cada um.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

COLUNAS_PREVISAO = ("data_referencia", "previsao", "intervalo_inferior", "intervalo_superior")


class ModeloSerie(ABC):
    """Interface que toda classe de modelo de série temporal do projeto implementa."""

    @abstractmethod
    def fit(self, serie_treino: pd.Series, exogena_treino: pd.Series | None = None) -> ModeloSerie:
        """Ajusta o modelo a uma série de treino (indexada por `data_referencia`).
        Retorna `self`, para permitir encadeamento (`modelo = Modelo().fit(serie)`)."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, horizonte: int, exogena_futura: pd.Series | None = None) -> pd.DataFrame:
        """Produz `horizonte` passos de previsão à frente do fim da série de treino.

        Returns:
            DataFrame com as colunas de `COLUNAS_PREVISAO`. Modelos que não estimam
            incerteza nativamente (ex.: naive) ainda devem preencher
            `intervalo_inferior`/`intervalo_superior` com alguma estimativa
            documentada (ex.: baseada no desvio-padrão dos resíduos de treino). Todo cenário
            projetado inclui intervalo de predição explícito, o que vale também para
            as previsões de validação.
        """
        raise NotImplementedError


def validar_saida_previsao(df: pd.DataFrame) -> None:
    """Confere que uma saída de `predict()` respeita o contrato mínimo — usado nos
    testes de cada modelo e no harness de validação, não repetido em cada `predict()`."""
    faltantes = [c for c in COLUNAS_PREVISAO if c not in df.columns]
    if faltantes:
        raise ValueError(f"saída de predict() não tem as colunas obrigatórias: {faltantes}")
    if (df["intervalo_inferior"] > df["intervalo_superior"]).any():
        raise ValueError("intervalo_inferior maior que intervalo_superior em pelo menos uma linha")
