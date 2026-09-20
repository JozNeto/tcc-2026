"""Indicador composto de exposição territorial e caracterização descritiva de
municípios (spec 02, Recortes 1 e 2 — Etapa 7 da proposta).

**Restrições inegociáveis (specs/constitution.md §5):** este módulo nunca projeta
cenários (proibido no Recorte 1) e nunca modela/prevê nada (proibido no Recorte 2).
Toda saída deste módulo carrega `exploratorio=True` — o indicador composto é uma
aproximação por fontes indiretas, não uma medição oficial (docs/00-proposta-resumo.md,
seção 2, "Advertência metodológica").
"""

from __future__ import annotations

import pandas as pd


class IndicadorTerritorialError(Exception):
    """Levantado quando os componentes e pesos informados são inconsistentes."""


def normalizar_min_max(serie: pd.Series) -> pd.Series:
    """Normaliza para [0, 1]. Uma série sem variação (todas as UFs empatadas) não
    tem "mais exposta" nem "menos exposta" — retorna 0.5 (neutro) para todas, em vez
    de produzir NaN por divisão por zero."""
    minimo, maximo = serie.min(), serie.max()
    if maximo == minimo:
        return pd.Series(0.5, index=serie.index)
    return (serie - minimo) / (maximo - minimo)


def construir_indicador_composto(
    componentes: dict[str, pd.Series], pesos: dict[str, float] | None = None
) -> pd.DataFrame:
    """Combina componentes de escalas diferentes (ex.: interesse no Google Trends,
    valor per capita de Bolsa Família) num indicador composto único por unidade
    territorial (Recorte 1 = UF).

    Args:
        componentes: nome_componente -> Series indexada pela unidade territorial
            (ex.: sigla de UF), valores brutos.
        pesos: nome_componente -> peso relativo; pesos iguais se não informado.
            Deve cobrir exatamente o mesmo conjunto de chaves de `componentes`.

    Returns:
        DataFrame indexado pela unidade territorial, com uma coluna por componente
        normalizado, `indicador_composto` (média ponderada dos componentes
        normalizados, em [0, 1]) e `exploratorio=True` em todas as linhas.

    Raises:
        IndicadorTerritorialError: se `pesos` não cobrir exatamente os componentes
            informados, ou se `componentes` estiver vazio.
    """
    if not componentes:
        raise IndicadorTerritorialError("nenhum componente informado")

    pesos = pesos or {nome: 1.0 for nome in componentes}
    if set(pesos) != set(componentes):
        raise IndicadorTerritorialError(
            f"pesos ({set(pesos)}) devem cobrir exatamente os componentes informados ({set(componentes)})"
        )

    tabela = pd.DataFrame({nome: normalizar_min_max(serie) for nome, serie in componentes.items()})

    soma_pesos = sum(pesos.values())
    tabela["indicador_composto"] = sum(tabela[nome] * peso for nome, peso in pesos.items()) / soma_pesos
    tabela["exploratorio"] = True
    return tabela


def identificar_uf_maior_exposicao(indicador_composto: pd.DataFrame) -> str:
    """Retorna a unidade territorial (índice do DataFrame) com maior
    `indicador_composto` — ordenamento comparativo, nunca projeção
    (specs/constitution.md §5: "sem projeção" no Recorte 1)."""
    return indicador_composto["indicador_composto"].idxmax()


def caracterizar_municipios(
    dados_municipio_long: pd.DataFrame,
    coluna_municipio: str = "unidade",
    coluna_variavel: str = "variavel",
    coluna_valor: str = "valor",
    coluna_data: str = "data_referencia",
) -> pd.DataFrame:
    """Caracterização puramente descritiva dos municípios da UF identificada
    (Recorte 2) — média, desvio-padrão e valor mais recente por variável.
    **Nunca ajusta modelo nem projeta** (specs/constitution.md §5: "sem modelagem"
    no Recorte 2).

    Args:
        dados_municipio_long: long-format (contrato de specs/01-ingestao-dados/spec.md),
            já restrito aos municípios da UF de interesse.

    Returns:
        DataFrame indexado por (município, variável) com colunas `media`,
        `desvio_padrao`, `valor_mais_recente`, `data_mais_recente`.
    """
    if dados_municipio_long.empty:
        return pd.DataFrame(
            columns=["media", "desvio_padrao", "valor_mais_recente", "data_mais_recente"]
        )

    agrupado = dados_municipio_long.groupby([coluna_municipio, coluna_variavel])

    resumo = agrupado[coluna_valor].agg(media="mean", desvio_padrao="std")

    idx_mais_recente = dados_municipio_long.groupby([coluna_municipio, coluna_variavel])[coluna_data].idxmax()
    linhas_mais_recentes = dados_municipio_long.loc[idx_mais_recente].set_index([coluna_municipio, coluna_variavel])

    resumo["valor_mais_recente"] = linhas_mais_recentes[coluna_valor]
    resumo["data_mais_recente"] = linhas_mais_recentes[coluna_data]

    return resumo
