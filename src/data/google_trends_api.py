"""Coleta do Google Trends via biblioteca `pytrends` (API não oficial).

Exceção documentada: não há API oficial do Google Trends e a exportação manual foi
substituída por esta coleta, com poucas chamadas e pausa longa entre elas. Depende de um
endpoint não oficial que pode mudar ou limitar acessos; falha de forma explícita, nunca
preenche valores. O índice é relativo (0–100) por consulta e mede interesse de busca, não
volume de apostas.
"""

from __future__ import annotations

import datetime as dt
import time

import pandas as pd

UFS_BR = {
    "BR-AC": "AC", "BR-AL": "AL", "BR-AM": "AM", "BR-AP": "AP", "BR-BA": "BA", "BR-CE": "CE",
    "BR-DF": "DF", "BR-ES": "ES", "BR-GO": "GO", "BR-MA": "MA", "BR-MG": "MG", "BR-MS": "MS",
    "BR-MT": "MT", "BR-PA": "PA", "BR-PB": "PB", "BR-PE": "PE", "BR-PI": "PI", "BR-PR": "PR",
    "BR-RJ": "RJ", "BR-RN": "RN", "BR-RS": "RS", "BR-RO": "RO", "BR-RR": "RR", "BR-SC": "SC",
    "BR-SE": "SE", "BR-SP": "SP", "BR-TO": "TO",
}


class TrendsError(Exception):
    """Falha real de coleta do Google Trends."""


def _cliente():
    try:
        from pytrends.request import TrendReq
    except ImportError as exc:  # pragma: no cover
        raise TrendsError("biblioteca pytrends não instalada") from exc
    # retries=0/backoff=0: contorna incompatibilidade do pytrends com urllib3 recente.
    return TrendReq(hl="pt-BR", tz=180, timeout=(10, 30), retries=0, backoff_factor=0)


def coletar_temporal(termos: list[str], inicio: str, fim: str, cliente=None) -> pd.DataFrame:
    """Série mensal nacional dos termos (mesma escala 0–100 entre os termos)."""
    py = cliente or _cliente()
    py.build_payload(termos, geo="BR", timeframe=f"{inicio} {fim}")
    df = py.interest_over_time()
    if df.empty:
        raise TrendsError("Trends devolveu série temporal vazia")
    df = df.drop(columns=["isPartial"], errors="ignore")
    longo = df.reset_index().melt(id_vars="date", var_name="termo", value_name="valor")
    longo["data_referencia"] = pd.to_datetime(longo["date"]).dt.date
    return longo[["data_referencia", "termo", "valor"]]


def coletar_regional(termo: str, inicio: str, fim: str, cliente=None) -> pd.DataFrame:
    """Interesse por UF (0–100 relativo ao maior valor entre as UFs, por termo)."""
    py = cliente or _cliente()
    py.build_payload([termo], geo="BR", timeframe=f"{inicio} {fim}")
    reg = py.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=True)
    if reg.empty:
        raise TrendsError(f"Trends devolveu recorte regional vazio para '{termo}'")
    reg = reg.reset_index()
    reg["uf"] = reg["geoCode"].map(UFS_BR)
    if reg["uf"].isna().any() or len(reg) != 27:
        raise TrendsError(f"recorte regional inesperado para '{termo}': {len(reg)} linhas")
    reg["termo"] = termo
    return reg.rename(columns={termo: "valor"})[["uf", "termo", "valor"]]


def coletar_tudo(termos: list[str], inicio: str, fim: str, pausa: float = 15.0, dormir=time.sleep):
    """1 chamada temporal e 1 regional POR TERMO, com pausa entre elas.

    Cada termo é consultado sozinho (escala 0–100 própria). Consultar termos juntos
    comprime a escala dos menos buscados: "jogo do tigrinho" (pico em 2023–2024) reduzia
    "apostas online" a valores 0/1 e produzia regressões espúrias."""
    cliente = _cliente()
    temporais, regionais = [], []
    for termo in termos:
        temporais.append(coletar_temporal([termo], inicio, fim, cliente))
        dormir(pausa)
        regionais.append(coletar_regional(termo, inicio, fim, cliente))
        dormir(pausa)
    temporal = pd.concat(temporais, ignore_index=True)
    meta = {"coletado_em": dt.datetime.now(dt.timezone.utc).isoformat(), "inicio": inicio, "fim": fim, "termos": termos}
    return temporal, pd.concat(regionais, ignore_index=True), meta
