"""Coleta real de tudo o que a análise da pergunta central usa (sem estimativas).

Fontes: SGS/BCB (crédito, inadimplência, Selic), IBGE/SIDRA (rendimento, desocupação,
população por UF) e Google Trends (interesse de busca por apostas, via pytrends).
Uso: python scripts/coletar_analise_central.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.data import google_trends_api as gt
from src.data import ibge, ibge_uf, sgs

CORTE = dt.date(2025, 12, 31)
TERMOS = ["apostas online", "bet", "jogo do tigrinho"]
SERIES_SGS = {
    "comprometimento_renda_pf": 29034,
    "endividamento_familias_sfn": 29037,
    "inadimplencia_pf_total": 21084,
    "inadimplencia_cartao_rotativo": 21127,
    "inadimplencia_cartao_total": 21129,
    "selic_acumulada_mes_anualizada": 4189,
    "ipca_variacao_mensal": 433,
}
TABELAS_IBGE = {
    "taxa_desocupacao": {"t": 6381, "n": "n1/all", "v": 4099},
    "rendimento_medio_real_habitual": {"t": 6390, "n": "n1/all", "v": 5933},
}


def main() -> None:
    pasta = RAIZ / "data" / "raw" / "analise_central"
    pasta.mkdir(parents=True, exist_ok=True)

    print("[SGS] coletando...")
    sgs.coletar(CORTE, series=SERIES_SGS).to_parquet(pasta / "sgs.parquet", index=False)

    print("[IBGE nacional] coletando...")
    ibge.coletar(CORTE, tabelas=TABELAS_IBGE).to_parquet(pasta / "ibge_nacional.parquet", index=False)

    print("[IBGE por UF] população 2025 e rendimento médio real (4º trimestre 2025, tabela 5436)...")
    ibge_uf.coletar_por_uf(6579, 9324, "2025").to_parquet(pasta / "uf_populacao_2025.parquet", index=False)
    ibge_uf.coletar_por_uf(5436, 5933, "202504").to_parquet(pasta / "uf_rendimento_2025T4.parquet", index=False)

    print("[Google Trends] 1 temporal + 1 regional por termo, pausa de 15 s entre chamadas...")
    temporal, regional, meta = gt.coletar_tudo(TERMOS, "2020-01-01", "2025-12-31", pausa=15.0)
    temporal.to_parquet(pasta / "trends_temporal.parquet", index=False)
    regional.to_parquet(pasta / "trends_regional.parquet", index=False)
    (pasta / "trends_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Concluído. Arquivos em", pasta)


if __name__ == "__main__":
    main()
