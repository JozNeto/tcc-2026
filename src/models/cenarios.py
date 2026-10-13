"""Projeção de cenários: inercial, contenção e
expansão, horizonte principal de 24 meses, com intervalos de predição explícitos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.base import ModeloSerie

HORIZONTE_PRINCIPAL_MESES = 24


def projetar_cenarios(
    modelo: ModeloSerie,
    horizonte: int = HORIZONTE_PRINCIPAL_MESES,
    exogena_futura: pd.Series | None = None,
    fator_contencao: float = 0.85,
    fator_expansao: float = 1.15,
) -> pd.DataFrame:
    """Projeta os três cenários a partir de um modelo já ajustado
    (`modelo.fit(...)` deve ter sido chamado antes).

    O cenário **inercial** é a previsão direta do modelo — condicional à manutenção
    do ambiente regulatório vigente, premissa que a
    é reconhecidamente frágil. Os
    cenários **contenção** e **expansão** aplicam um fator multiplicativo simples
    sobre a previsão pontual e o intervalo do cenário inercial — são exercícios de
    sensibilidade explícitos, não reajustes de modelo.

    Args:
        modelo: instância de `ModeloSerie` já ajustada.
        horizonte: nº de meses a projetar. Passos além de `HORIZONTE_PRINCIPAL_MESES`
            são rotulados `tipo="exercicio_de_cenario"` em vez de `"previsao"`
.
        exogena_futura: ver `ModeloSerie.predict`.
        fator_contencao: multiplicador aplicado à previsão/intervalo no cenário de
            contenção (< 1.0 = trajetória mais baixa que a inercial).
        fator_expansao: idem, para o cenário de expansão (> 1.0).

    Returns:
        DataFrame concatenando os 3 cenários, com colunas adicionais `cenario`,
        `condicional_a_regulacao_estavel`, `tipo` e `passo` (nº do mês projetado,
        1-indexado).
    """
    inercial = modelo.predict(horizonte, exogena_futura).copy()
    inercial["passo"] = np.arange(1, horizonte + 1)
    inercial["cenario"] = "inercial"
    inercial["condicional_a_regulacao_estavel"] = True

    def _cenario_ajustado(nome: str, fator: float) -> pd.DataFrame:
        cenario = inercial.copy()
        cenario["cenario"] = nome
        cenario["condicional_a_regulacao_estavel"] = False
        for coluna in ("previsao", "intervalo_inferior", "intervalo_superior"):
            cenario[coluna] = inercial[coluna] * fator
        return cenario

    resultado = pd.concat(
        [inercial, _cenario_ajustado("contencao", fator_contencao), _cenario_ajustado("expansao", fator_expansao)],
        ignore_index=True,
    )
    resultado["tipo"] = np.where(resultado["passo"] <= HORIZONTE_PRINCIPAL_MESES, "previsao", "exercicio_de_cenario")
    return resultado
