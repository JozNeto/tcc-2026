"""Tratamento da base nacional: deflacionamento IPCA, imputação de ausências e
sinalização de outliers (spec 02, critério 1).

Implementa `specs/02-limpeza-eda/spec.md`, seção "Tratamento". Não decide sozinho o
que fazer com um outlier sinalizado — apenas sinaliza (specs/constitution.md, "Casos
de borda": outlier genuíno não deve ser removido silenciosamente).

Convenção de entrada: DataFrame long-format (contrato de `specs/01-ingestao-dados/spec.md`).
Convenção de saída: DataFrame wide-format (uma linha por `data_referencia`, uma coluna
por variável, mais colunas `<variavel>_imputado` e `<variavel>_outlier`), conforme
`specs/02-limpeza-eda/spec.md`, seção "Contrato de dados".
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd


class TratamentoError(Exception):
    """Levantado quando uma etapa de tratamento recebe entrada incompatível com o
    contrato de dados esperado (ex.: série de IPCA vazia)."""


def construir_indice_deflator(ipca_variacao_mensal: pd.DataFrame, data_base: dt.date) -> pd.Series:
    """Constrói um índice de preços acumulado a partir da série de variação mensal
    do IPCA (contrato long-format, `variavel="ipca_variacao_mensal"`), ancorado em
    100 na `data_base`.

    Args:
        ipca_variacao_mensal: DataFrame long-format com colunas `data_referencia` e
            `valor` (variação mensal em %, ex.: 0.58 significa 0,58%).
        data_base: mês cujo índice vale exatamente 100 (mês de referência dos valores
            "reais" produzidos por `deflacionar`).

    Returns:
        `pd.Series` indexada por `data_referencia`, valor = índice de preços.

    Raises:
        TratamentoError: se a série de entrada estiver vazia ou não cobrir `data_base`.
    """
    if ipca_variacao_mensal.empty:
        raise TratamentoError("série de variação mensal do IPCA está vazia")

    serie = (
        ipca_variacao_mensal.sort_values("data_referencia")
        .set_index("data_referencia")["valor"]
        .astype(float)
    )
    fator_mensal = 1 + serie / 100.0

    if data_base not in fator_mensal.index:
        raise TratamentoError(f"data_base {data_base} não está coberta pela série de IPCA")

    indice = pd.Series(index=fator_mensal.index, dtype=float)
    indice.loc[data_base] = 100.0

    datas_apos = [d for d in fator_mensal.index if d > data_base]
    valor_atual = 100.0
    for data in datas_apos:
        valor_atual *= fator_mensal.loc[data]
        indice.loc[data] = valor_atual

    datas_antes = sorted((d for d in fator_mensal.index if d < data_base), reverse=True)
    valor_atual = 100.0
    for data in datas_antes:
        data_seguinte = min((d for d in fator_mensal.index if d > data), default=data_base)
        valor_atual /= fator_mensal.loc[data_seguinte]
        indice.loc[data] = valor_atual

    return indice.sort_index()


def deflacionar(serie_nominal: pd.Series, indice_deflator: pd.Series) -> pd.Series:
    """Converte uma série nominal (indexada por data) em valores reais, na base do
    índice construído por `construir_indice_deflator` (100 = preços da data_base).
    """
    indice_alinhado = indice_deflator.reindex(serie_nominal.index)
    if indice_alinhado.isna().any():
        faltantes = indice_alinhado[indice_alinhado.isna()].index.tolist()
        raise TratamentoError(f"índice deflator não cobre as datas: {faltantes}")
    return serie_nominal * (100.0 / indice_alinhado)


def imputar_gaps_curtos(serie: pd.Series, limite_gap: int = 2) -> tuple[pd.Series, pd.Series]:
    """Interpola linearmente ausências curtas (até `limite_gap` observações
    consecutivas) e deixa ausências mais longas (ex.: série com início tardio) como
    `NaN` — specs/02-limpeza-eda/spec.md, "Casos de borda": gap estrutural não deve
    ser imputado retroativamente.

    Returns:
        Tupla `(serie_tratada, mascara_imputado)` — `mascara_imputado[i]` é `True`
        onde o valor foi preenchido por interpolação.
    """
    ausente = serie.isna()
    # `pandas.Series.interpolate(limit=...)` limita quantos NaNs consecutivos são
    # preenchidos A PARTIR DA BORDA do gap — não descarta o gap inteiro quando ele é
    # maior que o limite. Para o comportamento exigido pela spec ("gap com até
    # `limite_gap` observações" é tudo-ou-nada), precisamos identificar cada run de
    # NaN consecutivo e decidir por run, não por posição individual.
    interpolada_interior = serie.interpolate(method="linear", limit_area="inside")
    bloco = (ausente != ausente.shift()).cumsum()
    tamanho_run = ausente.groupby(bloco).transform("size").where(ausente, 0)

    elegivel = ausente & (tamanho_run > 0) & (tamanho_run <= limite_gap)

    resultado = serie.copy()
    resultado[elegivel] = interpolada_interior[elegivel]
    mascara_imputado = elegivel & resultado.notna()
    return resultado, mascara_imputado


def sinalizar_outliers(serie: pd.Series, n_desvios: float = 3.0) -> pd.Series:
    """Sinaliza valores a mais de `n_desvios` desvios-padrão da média da série.
    Não remove nem substitui nada — apenas retorna a máscara booleana."""
    media, desvio = serie.mean(), serie.std()
    if not desvio or np.isnan(desvio):
        return pd.Series(False, index=serie.index)
    return (serie - media).abs() > (n_desvios * desvio)


def tratar(
    base_long: pd.DataFrame,
    ipca_variacao_mensal: pd.DataFrame,
    data_base_deflacao: dt.date,
    variaveis_monetarias: set[str],
    limite_gap_imputacao: int = 2,
    n_desvios_outlier: float = 3.0,
) -> pd.DataFrame:
    """Orquestra o tratamento completo: pivota para wide-format, deflaciona as
    variáveis monetárias, imputa gaps curtos e sinaliza outliers em todas as colunas.

    Args:
        base_long: base bruta consolidada, long-format (ver specs/01-ingestao-dados/spec.md).
        ipca_variacao_mensal: ver `construir_indice_deflator`.
        data_base_deflacao: ver `construir_indice_deflator`.
        variaveis_monetarias: nomes de variáveis em R$ que devem ser deflacionadas —
            percentuais, índices e contagens **não** entram aqui (decisão explícita
            de quem chama, não inferida por heurística de nome).
        limite_gap_imputacao: ver `imputar_gaps_curtos`.
        n_desvios_outlier: ver `sinalizar_outliers`.

    Returns:
        DataFrame wide-format com uma coluna por variável mais
        `<variavel>_imputado` e `<variavel>_outlier`, indexado por `data_referencia`.
    """
    indice_deflator = construir_indice_deflator(ipca_variacao_mensal, data_base_deflacao)

    wide = base_long.pivot_table(index="data_referencia", columns="variavel", values="valor", aggfunc="first")

    colunas_tratadas: dict[str, pd.Series] = {}
    colunas_imputado: dict[str, pd.Series] = {}
    colunas_outlier: dict[str, pd.Series] = {}

    for variavel in wide.columns:
        serie = wide[variavel]
        if variavel in variaveis_monetarias:
            serie = deflacionar(serie.dropna(), indice_deflator).reindex(serie.index)

        serie_tratada, mascara_imputado = imputar_gaps_curtos(serie, limite_gap_imputacao)
        colunas_tratadas[variavel] = serie_tratada
        colunas_imputado[f"{variavel}_imputado"] = mascara_imputado
        colunas_outlier[f"{variavel}_outlier"] = sinalizar_outliers(serie_tratada.dropna()).reindex(
            serie_tratada.index, fill_value=False
        )

    resultado = pd.concat(
        [pd.DataFrame(colunas_tratadas), pd.DataFrame(colunas_imputado), pd.DataFrame(colunas_outlier)],
        axis=1,
    )
    return resultado.sort_index()
