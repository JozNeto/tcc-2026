"""Coleta de séries do SGS/BCB — Sistema Gerenciador de Séries Temporais.

Cobre a camada "Núcleo": endividamento das famílias, comprometimento de
renda e inadimplência da carteira de pessoas físicas, mais o IPCA (série 433, variação
mensal), usado por `src/features/tratamento.py` para deflacionar as demais séries
nominais do projeto.

Fonte oficial com API REST pública e estável — nenhuma necessidade de scraping.
Documentação da API: https://dadosabertos.bcb.gov.br/

Os códigos de série abaixo foram verificados manualmente contra o Portal de Dados
Abertos do BCB e uma consulta real à API. Séries do SGS podem ser descontinuadas
e substituídas ao longo do tempo — antes de uma nova rodada de coleta em produção,
reconfirme os códigos em https://dadosabertos.bcb.gov.br/.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

FONTE = "SGS/BCB"
BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
COLUNAS_SAIDA = ("data_referencia", "unidade", "variavel", "valor", "fonte", "coletado_em")

# nome_variavel -> código SGS. As séries antigas 19881/19882 foram descontinuadas pelo BCB.
SERIES = {
    "comprometimento_renda_pf": 29034,
    "endividamento_familias_sfn": 29037,
    "inadimplencia_pf": 21084,
    "ipca_variacao_mensal": 433,
}


class ColetaSGSError(Exception):
    """Levantado quando a API do SGS falha ou retorna algo fora do esperado.

    Nunca é engolida silenciosamente.
    """


def _formatar_data_br(data: dt.date) -> str:
    return data.strftime("%d/%m/%Y")


def _requisitar_serie(codigo: int, data_inicial: dt.date | None, data_final: dt.date) -> list[dict]:
    params: dict[str, str] = {"formato": "json", "dataFinal": _formatar_data_br(data_final)}
    if data_inicial is not None:
        params["dataInicial"] = _formatar_data_br(data_inicial)

    url = BASE_URL.format(codigo=codigo)
    try:
        resposta = requests.get(url, params=params, timeout=30)
        resposta.raise_for_status()
    except requests.RequestException as exc:
        raise ColetaSGSError(f"falha ao consultar série SGS {codigo}: {exc}") from exc

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise ColetaSGSError(f"resposta não-JSON da série SGS {codigo}: {resposta.text[:200]!r}") from exc

    if not isinstance(dados, list):
        raise ColetaSGSError(f"resposta inesperada da série SGS {codigo}: {dados!r}")
    return dados


def _parse_serie(
    dados: list[dict], nome_variavel: str, codigo: int, coletado_em: dt.datetime
) -> pd.DataFrame:
    if not dados:
        return pd.DataFrame(columns=list(COLUNAS_SAIDA))

    df = pd.DataFrame(dados)
    df["data_referencia"] = pd.to_datetime(df["data"], format="%d/%m/%Y").dt.date
    df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
    df["unidade"] = "BR"
    df["variavel"] = nome_variavel
    df["fonte"] = f"{FONTE} (série {codigo})"
    df["coletado_em"] = coletado_em
    return df[list(COLUNAS_SAIDA)]


def coletar(
    data_corte: dt.date,
    data_inicial: dt.date | None = None,
    series: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Coleta as séries do SGS/BCB do núcleo nacional.

    Args:
        data_corte: data-limite de referência. Nenhuma
            linha com `data_referencia` posterior a esta entra na saída — a API já é
            consultada com `dataFinal=data_corte`, e o resultado é filtrado de novo
            no cliente por segurança.
        data_inicial: início da janela de consulta; se `None`, retorna o histórico
            completo disponível de cada série.
        series: mapeamento `nome_variavel -> código SGS`; usa `SERIES` (catálogo
            padrão do módulo) se não informado.

    Returns:
        DataFrame long-format no formato long-format do projeto.

    Raises:
        ColetaSGSError: se qualquer série falhar ao ser consultada ou parseada.
    """
    series = series or SERIES
    coletado_em = dt.datetime.now(dt.timezone.utc)

    partes = [
        _parse_serie(_requisitar_serie(codigo, data_inicial, data_corte), nome_variavel, codigo, coletado_em)
        for nome_variavel, codigo in series.items()
    ]

    resultado = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=list(COLUNAS_SAIDA))
    if not resultado.empty:
        resultado = resultado[resultado["data_referencia"] <= data_corte].reset_index(drop=True)
    return resultado
