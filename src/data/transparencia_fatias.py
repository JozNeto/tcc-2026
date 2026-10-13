"""Coleta do Novo Bolsa Família por município, em fatias pequenas e retomáveis.

A API do Portal da Transparência entrega um município por chamada. Para somar por UF
são necessárias ~5.570 chamadas por mês de referência. Para não estourar o limite de
requisições da chave pessoal, a coleta é feita em fatias: cada execução consulta no
máximo `tamanho_fatia` municípios, com pausa entre chamadas, grava o progresso em
disco e para na primeira resposta de limite de uso (HTTP 429/403). A execução
seguinte retoma de onde parou.

Nada é estimado: município sem registro na API é gravado como `sem_registro`, nunca
como zero.
"""

from __future__ import annotations

import datetime as dt
import os
import time
from pathlib import Path

import pandas as pd
import requests

URL_API = "https://api.portaldatransparencia.gov.br/api-de-dados/novo-bolsa-familia-por-municipio"
URL_MUNICIPIOS_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
TOKEN_ENV_VAR = "PORTAL_TRANSPARENCIA_TOKEN"
COLUNAS = ["codigo_ibge", "uf", "mes_ano", "status", "valor", "beneficiarios", "coletado_em"]
STATUS_LIMITE = (429, 403)


class LimiteDeUsoError(Exception):
    """A API sinalizou limite de uso; a coleta deve parar e ser retomada depois."""


class TransparenciaFatiasError(Exception):
    """Falha real de coleta (token ausente, resposta inesperada)."""


def listar_municipios_ibge(cache: Path | None = None, tentativas: int = 3, dormir=time.sleep) -> pd.DataFrame:
    """Lista oficial de municípios (código IBGE de 7 dígitos e UF) via API do IBGE.
    Se `cache` existir, lê dele (a lista não muda entre fatias); senão consulta a API
    com poucas tentativas e grava o cache."""
    if cache is not None and cache.exists():
        return pd.read_csv(cache, dtype={"codigo_ibge": str})

    resposta = None
    for i in range(tentativas):
        try:
            resposta = requests.get(URL_MUNICIPIOS_IBGE, timeout=60)
            resposta.raise_for_status()
            break
        except requests.RequestException as exc:
            if i == tentativas - 1:
                raise TransparenciaFatiasError(f"falha ao listar municípios do IBGE: {exc}") from exc
            dormir(10 * (i + 1))
    linhas = []
    for m in resposta.json():
        uf = (
            (m.get("microrregiao") or {}).get("mesorregiao", {}).get("UF", {}).get("sigla")
            or (m.get("regiao-imediata") or {}).get("regiao-intermediaria", {}).get("UF", {}).get("sigla")
        )
        linhas.append({"codigo_ibge": str(m["id"]), "uf": uf})
    df = pd.DataFrame(linhas)
    if df["uf"].isna().any():
        raise TransparenciaFatiasError("município sem UF na resposta do IBGE")
    df = df.sort_values("codigo_ibge").reset_index(drop=True)
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False)
    return df


def _token() -> str:
    token = os.environ.get(TOKEN_ENV_VAR)
    if not token:
        raise TransparenciaFatiasError(f"variável {TOKEN_ENV_VAR} não configurada")
    return token


def consultar_municipio(codigo_ibge: str, mes_ano: str) -> list[dict]:
    """Uma chamada (com paginação) para um município. Levanta `LimiteDeUsoError` em
    HTTP 429/403 e `TransparenciaFatiasError` em qualquer outra falha."""
    registros: list[dict] = []
    for pagina in range(1, 6):
        r = None
        for tentativa in range(3):
            try:
                r = requests.get(
                    URL_API,
                    params={"mesAno": mes_ano, "codigoIbge": codigo_ibge, "pagina": pagina},
                    headers={"chave-api-dados": _token()},
                    timeout=30,
                )
                break
            except requests.RequestException as exc:
                if tentativa == 2:
                    raise TransparenciaFatiasError(f"falha de rede em {codigo_ibge}: {exc}") from exc
                time.sleep(15 * (tentativa + 1))
        if r.status_code in STATUS_LIMITE:
            raise LimiteDeUsoError(f"HTTP {r.status_code} ao consultar {codigo_ibge}")
        if r.status_code != 200:
            raise TransparenciaFatiasError(f"HTTP {r.status_code} ao consultar {codigo_ibge}")
        dados = r.json()
        if not isinstance(dados, list):
            raise TransparenciaFatiasError(f"resposta inesperada em {codigo_ibge}: {dados!r}")
        registros.extend(dados)
        if len(dados) < 15:
            break
    return registros


def ler_progresso(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame(columns=COLUNAS)
    return pd.read_csv(caminho, dtype={"codigo_ibge": str, "mes_ano": str})


def coletar_fatia(
    municipios: pd.DataFrame,
    mes_ano: str,
    caminho_progresso: Path,
    tamanho_fatia: int = 150,
    pausa_segundos: float = 1.5,
    consultar=consultar_municipio,
    dormir=time.sleep,
) -> dict:
    """Consulta até `tamanho_fatia` municípios ainda não coletados e acrescenta o
    resultado ao arquivo de progresso. Retorna um resumo da execução."""
    feitos = set(ler_progresso(caminho_progresso)["codigo_ibge"])
    pendentes = municipios[~municipios["codigo_ibge"].isin(feitos)]
    fatia = pendentes.head(tamanho_fatia)

    caminho_progresso.parent.mkdir(parents=True, exist_ok=True)
    novos = 0
    parou_por_limite = False
    for _, m in fatia.iterrows():
        try:
            registros = consultar(m["codigo_ibge"], mes_ano)
        except LimiteDeUsoError:
            parou_por_limite = True
            break

        agora = dt.datetime.now(dt.timezone.utc).isoformat()
        if registros:
            linha = {
                "status": "ok",
                "valor": sum(float(x.get("valor") or 0) for x in registros),
                "beneficiarios": sum(float(x.get("quantidadeBeneficiados") or 0) for x in registros),
            }
        else:
            linha = {"status": "sem_registro", "valor": None, "beneficiarios": None}
        linha.update({"codigo_ibge": m["codigo_ibge"], "uf": m["uf"], "mes_ano": mes_ano, "coletado_em": agora})

        pd.DataFrame([linha])[COLUNAS].to_csv(
            caminho_progresso, mode="a", header=not caminho_progresso.exists(), index=False
        )
        novos += 1
        dormir(pausa_segundos)

    return {
        "coletados_nesta_execucao": novos,
        "total_feitos": len(feitos) + novos,
        "total_municipios": len(municipios),
        "parou_por_limite": parou_por_limite,
    }


def agregar_por_uf(caminho_progresso: Path) -> pd.DataFrame:
    """Soma por UF apenas os municípios coletados, informando a cobertura — nunca
    apresenta como total da UF uma soma parcial sem sinalizar."""
    df = ler_progresso(caminho_progresso)
    ok = df[df["status"] == "ok"]
    agregado = ok.groupby("uf").agg(
        valor_repassado=("valor", "sum"),
        beneficiarios=("beneficiarios", "sum"),
        municipios_com_registro=("codigo_ibge", "count"),
    )
    agregado["municipios_coletados"] = df.groupby("uf")["codigo_ibge"].count()
    return agregado.reset_index()
