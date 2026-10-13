"""Séries do IBGE/SIDRA em nível de Unidade da Federação (n3)."""

from __future__ import annotations

import pandas as pd
import requests

BASE = "https://apisidra.ibge.gov.br/values"

COD_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO", 21: "MA", 22: "PI",
    23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA", 31: "MG", 32: "ES",
    33: "RJ", 35: "SP", 41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


class IbgeUfError(Exception):
    """Falha real ao consultar o SIDRA por UF."""


def coletar_por_uf(tabela: int, variavel: int, periodo: str) -> pd.DataFrame:
    """Valor da `variavel` da `tabela` para as 27 UFs no `periodo` (código SIDRA, ex.: '2025'
    ou '202512')."""
    url = f"{BASE}/t/{tabela}/n3/all/v/{variavel}/p/{periodo}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dados = r.json()
    except (requests.RequestException, ValueError) as exc:
        raise IbgeUfError(f"falha ao consultar {url}: {exc}") from exc

    linhas = []
    for item in dados[1:]:
        uf = COD_UF.get(int(item["D1C"]))
        if uf is None:
            raise IbgeUfError(f"código de UF desconhecido: {item['D1C']}")
        linhas.append({"uf": uf, "periodo": item["D3C"], "valor": pd.to_numeric(item["V"], errors="coerce")})
    df = pd.DataFrame(linhas)
    if df["uf"].nunique() != 27:
        raise IbgeUfError(f"esperadas 27 UFs, recebidas {df['uf'].nunique()} (tabela {tabela}, período {periodo})")
    return df
