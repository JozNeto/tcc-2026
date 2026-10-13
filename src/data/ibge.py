"""Coleta de séries do IBGE via API SIDRA.

Fonte oficial com API REST pública e estável — nenhuma necessidade de scraping
. Documentação: https://apisidra.ibge.gov.br/

As tabelas/variáveis abaixo foram verificadas manualmente contra a API real em
2026-08-17:

- Tabela 6381, variável 4099: taxa de desocupação, PNAD Contínua, trimestre móvel (%).
- Tabela 8880, variável 7170, classificação 11046=56734: índice de volume de vendas
  no comércio varejista, PMC, com ajuste sazonal, base 2022=100.
- Tabela 6579, variável 9324: população residente estimada (pessoas), anual.

A API SIDRA usa periodicidades diferentes por tabela — mensal (`AAAAMM`), trimestre
móvel (`AAAAMM`, mês final do trimestre) ou anual (`AAAA`). Códigos de 4 dígitos
(anuais) são mapeados para 1º de julho do ano, convenção usada pelo próprio IBGE
para estimativas populacionais de referência.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

from src.data._comum import COLUNAS_SAIDA, filtrar_data_corte, montar_long

FONTE = "IBGE/SIDRA"
BASE_URL = "https://apisidra.ibge.gov.br/values"

# nome_variavel -> parâmetros da consulta SIDRA (ver docstring do módulo).
TABELAS: dict[str, dict] = {
    "taxa_desocupacao": {"t": 6381, "n": "n1/all", "v": 4099},
    "pmc_indice_volume_vendas_ajustado": {"t": 8880, "n": "n1/all", "v": 7170, "c11046": 56734},
    "populacao_estimada": {"t": 6579, "n": "n1/all", "v": 9324},
}


class ColetaIBGEError(Exception):
    """Levantado quando a API SIDRA falha ou retorna algo fora do esperado."""


def _montar_url(config: dict) -> str:
    partes = [f"t/{config['t']}", config["n"], f"v/{config['v']}", "p/all"]
    for chave, valor in config.items():
        if chave.startswith("c"):
            partes.append(f"{chave}/{valor}")
    return f"{BASE_URL}/{'/'.join(partes)}"


def _parse_periodo(codigo: str) -> dt.date:
    codigo = str(codigo)
    if len(codigo) == 4:  # anual (ex.: "2025")
        return dt.date(int(codigo), 7, 1)
    if len(codigo) == 6:  # mensal ou trimestre móvel (ex.: "202606")
        return dt.date(int(codigo[:4]), int(codigo[4:6]), 1)
    raise ColetaIBGEError(f"formato de período SIDRA não reconhecido: {codigo!r}")


def _requisitar_tabela(nome_variavel: str, config: dict) -> list[dict]:
    url = _montar_url(config)
    try:
        resposta = requests.get(url, timeout=30)
        resposta.raise_for_status()
    except requests.RequestException as exc:
        raise ColetaIBGEError(f"falha ao consultar SIDRA para '{nome_variavel}': {exc}") from exc

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise ColetaIBGEError(
            f"resposta não-JSON do SIDRA para '{nome_variavel}': {resposta.text[:200]!r}"
        ) from exc

    if not isinstance(dados, list) or len(dados) < 1:
        raise ColetaIBGEError(f"resposta inesperada do SIDRA para '{nome_variavel}': {dados!r}")
    return dados[1:]  # primeira linha é o cabeçalho de descrição das colunas


def _parse_tabela(dados: list[dict], nome_variavel: str, config: dict, coletado_em: dt.datetime) -> pd.DataFrame:
    if not dados:
        return pd.DataFrame(columns=list(COLUNAS_SAIDA))

    datas = [_parse_periodo(linha["D3C"]) for linha in dados]
    valores = pd.to_numeric(pd.Series(linha["V"] for linha in dados), errors="coerce")
    return montar_long(
        datas=datas,
        valores=valores,
        variavel=nome_variavel,
        unidade="BR",
        fonte=f"{FONTE} (tabela {config['t']})",
        coletado_em=coletado_em,
    )


def coletar(data_corte: dt.date, tabelas: dict[str, dict] | None = None) -> pd.DataFrame:
    """Coleta as séries do IBGE/SIDRA usadas como controle socioeconômico do projeto.

    Args:
        data_corte: data-limite de referência.
        tabelas: mapeamento `nome_variavel -> config SIDRA`; usa `TABELAS` (catálogo
            padrão do módulo) se não informado.

    Returns:
        DataFrame long-format no formato long-format do projeto.

    Raises:
        ColetaIBGEError: se qualquer tabela falhar ao ser consultada ou parseada.
    """
    tabelas = tabelas or TABELAS
    coletado_em = dt.datetime.now(dt.timezone.utc)

    partes = [
        _parse_tabela(_requisitar_tabela(nome_variavel, config), nome_variavel, config, coletado_em)
        for nome_variavel, config in tabelas.items()
    ]

    resultado = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=list(COLUNAS_SAIDA))
    return filtrar_data_corte(resultado, data_corte)
