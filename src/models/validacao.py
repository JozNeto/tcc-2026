"""Validação por origem móvel (rolling origin / walk-forward).

**Único método de validação permitido no projeto**: nunca
embaralha observações nem faz split aleatório treino/teste, por se tratar de séries
temporais.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from src.models.base import ModeloSerie


def validar_rolling_origin(
    serie: pd.Series,
    construir_modelo: Callable[[], ModeloSerie],
    tamanho_minimo_treino: int,
    horizonte: int = 1,
    passo: int = 1,
    exogena: pd.Series | None = None,
) -> pd.DataFrame:
    """A cada origem, treina com todas as observações até ali e prevê `horizonte`
    passos à frente; a origem avança `passo` observações a cada iteração, até não
    caber mais um horizonte completo de teste na série.

    Args:
        serie: série completa (treino + teste), indexada por `data_referencia`.
        construir_modelo: fábrica sem argumentos que retorna uma nova instância de
            `ModeloSerie` a cada origem (evita reaproveitar estado entre origens).
        tamanho_minimo_treino: nº mínimo de observações antes da primeira origem.
        horizonte: nº de passos previstos a partir de cada origem.
        passo: quantas observações a origem avança a cada iteração.
        exogena: série exógena alinhada a `serie`, se o modelo exigir.

    Returns:
        DataFrame concatenando a saída de `predict()` de cada origem, mais as
        colunas `valor_real` e `origem` (posição da origem na série limpa).

    Raises:
        ValueError: se `tamanho_minimo_treino` + `horizonte` for maior que o
            tamanho da série (nenhuma origem possível).
    """
    serie_limpa = serie.dropna()
    resultados = []
    origem = tamanho_minimo_treino

    while origem + horizonte <= len(serie_limpa):
        treino = serie_limpa.iloc[:origem]
        real = serie_limpa.iloc[origem : origem + horizonte]
        exog_treino = exogena.iloc[:origem] if exogena is not None else None
        exog_futura = exogena.iloc[origem : origem + horizonte] if exogena is not None else None

        modelo = construir_modelo().fit(treino, exog_treino)
        previsao = modelo.predict(horizonte, exog_futura).copy()
        previsao["valor_real"] = real.to_numpy()
        previsao["origem"] = origem

        resultados.append(previsao)
        origem += passo

    if not resultados:
        raise ValueError(
            f"nenhuma origem possível: série tem {len(serie_limpa)} observações, "
            f"tamanho_minimo_treino={tamanho_minimo_treino}, horizonte={horizonte}"
        )
    return pd.concat(resultados, ignore_index=True)
