"""Coleta via API oficial do Portal da Transparência.

Fonte oficial com API REST documentada — requer token gratuito, nunca hardcoded
. Token vem da variável de ambiente
`PORTAL_TRANSPARENCIA_TOKEN` (ver `.env.example`); obtenha um cadastrando um e-mail em
https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email.

Endpoint verificado no OpenAPI spec real da API
(https://api.portaldatransparencia.gov.br/v3/api-docs) em 2026-08-17:
`/api-de-dados/novo-bolsa-familia-por-municipio`, parâmetros `mesAno` (AAAAMM),
`codigoIbge`, `pagina`. **Não existe** endpoint de agregado nacional ou por UF nesta
API — é por município. Agregações por UF (Recorte 1) somam os municípios daquela UF
.
"""

from __future__ import annotations

import datetime as dt
import os

import pandas as pd
import requests

from src.data._comum import COLUNAS_SAIDA, filtrar_data_corte

FONTE = "Portal da Transparência (Novo Bolsa Família)"
BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/novo-bolsa-familia-por-municipio"
TOKEN_ENV_VAR = "PORTAL_TRANSPARENCIA_TOKEN"


class ColetaTransparenciaError(Exception):
    """Levantado quando a API falha, retorna algo fora do esperado, ou o token de
    acesso não está configurado."""


def _token() -> str:
    token = os.environ.get(TOKEN_ENV_VAR)
    if not token:
        raise ColetaTransparenciaError(
            f"variável de ambiente {TOKEN_ENV_VAR} não configurada — solicite um "
            "token gratuito em https://portaldatransparencia.gov.br/api-de-dados/"
            "cadastrar-email e defina em .env (ver .env.example)."
        )
    return token


def _requisitar_municipio(codigo_ibge: str, mes_ano: str) -> list[dict]:
    try:
        resposta = requests.get(
            BASE_URL,
            params={"mesAno": mes_ano, "codigoIbge": codigo_ibge, "pagina": 1},
            headers={"chave-api-dados": _token()},
            timeout=30,
        )
        resposta.raise_for_status()
    except requests.RequestException as exc:
        raise ColetaTransparenciaError(
            f"falha ao consultar Portal da Transparência para município "
            f"{codigo_ibge}, {mes_ano}: {exc}"
        ) from exc

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise ColetaTransparenciaError(
            f"resposta não-JSON do Portal da Transparência: {resposta.text[:200]!r}"
        ) from exc

    if not isinstance(dados, list):
        raise ColetaTransparenciaError(f"resposta inesperada do Portal da Transparência: {dados!r}")
    return dados


def _somar_valor_e_beneficiarios(dados: list[dict]) -> tuple[float, float]:
    """Soma valor e quantidade de beneficiários — a API pode paginar/segmentar
    múltiplos registros por município/mês (ex.: por faixa etária)."""
    valor_total = sum(float(item.get("valor", 0) or 0) for item in dados)
    quantidade_total = sum(float(item.get("quantidadeBeneficiados", 0) or 0) for item in dados)
    return valor_total, quantidade_total


def coletar(
    data_corte: dt.date,
    codigos_ibge_municipio: list[str],
    data_inicial: dt.date | None = None,
) -> pd.DataFrame:
    """Coleta valores repassados e nº de beneficiários do Novo Bolsa Família por
    município, mês a mês, para os municípios informados.

    Args:
        data_corte: data-limite de referência.
        codigos_ibge_municipio: códigos IBGE dos municípios a consultar. A API não
            oferece agregado nacional/UF — quem precisar de um agregado por UF deve
            informar todos os municípios daquela UF.
        data_inicial: primeiro mês a consultar; se `None`, usa 24 meses antes de
            `data_corte` (a API exige iterar mês a mês, não tem modo "histórico completo").

    Returns:
        DataFrame long-format, `unidade` = código IBGE do município, `variavel` em
        {"bolsa_familia_valor_repassado", "bolsa_familia_beneficiarios"}.

    Raises:
        ColetaTransparenciaError: se o token não estiver configurado ou a API falhar.
    """
    if data_inicial is None:
        data_inicial = dt.date(data_corte.year - 2, data_corte.month, 1)

    meses = pd.period_range(start=data_inicial, end=data_corte, freq="M")
    coletado_em = dt.datetime.now(dt.timezone.utc)

    linhas = []
    for codigo_ibge in codigos_ibge_municipio:
        for periodo in meses:
            mes_ano = periodo.strftime("%Y%m")
            dados = _requisitar_municipio(codigo_ibge, mes_ano)
            valor_total, quantidade_total = _somar_valor_e_beneficiarios(dados)
            data_referencia = periodo.to_timestamp().date()
            linhas.append((data_referencia, codigo_ibge, "bolsa_familia_valor_repassado", valor_total))
            linhas.append((data_referencia, codigo_ibge, "bolsa_familia_beneficiarios", quantidade_total))

    if not linhas:
        return pd.DataFrame(columns=list(COLUNAS_SAIDA))

    df = pd.DataFrame(linhas, columns=["data_referencia", "unidade", "variavel", "valor"])
    df["fonte"] = FONTE
    df["coletado_em"] = coletado_em
    return filtrar_data_corte(df[list(COLUNAS_SAIDA)], data_corte)
