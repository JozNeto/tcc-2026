"""Coleta real das fontes de API do núcleo nacional.

Roda a coleta de verdade contra as APIs públicas do SGS/BCB e do IBGE/SIDRA (sem
necessidade de chave) e, se PORTAL_TRANSPARENCIA_TOKEN estiver configurado, avisa
que essa fonte ainda precisa de uma lista de municípios para ser executada (ver
src/data/transparencia.py — é uma API por município, não tem agregado nacional).

Não inventa nem aproxima nenhum valor: se uma fonte falhar (rede, mudança de
schema), o script para com o erro real da coleta, não com um valor substituto.

Uso: `python scripts/coletar_nucleo.py`
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import ibge, sgs

DATA_CORTE = dt.date(2025, 12, 31)
SAIDA = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    print(f"Data de corte: {DATA_CORTE}")

    print("\n[SGS/BCB] coletando comprometimento de renda, endividamento, "
          "inadimplência PF e IPCA...")
    df_sgs = sgs.coletar(data_corte=DATA_CORTE)
    caminho_sgs = SAIDA / f"sgs_corte-{DATA_CORTE}_run-{timestamp}.parquet"
    df_sgs.to_parquet(caminho_sgs, index=False)
    print(f"  {len(df_sgs)} linhas, variáveis: {sorted(df_sgs['variavel'].unique())}")
    print(f"  salvo em {caminho_sgs}")

    print("\n[IBGE/SIDRA] coletando taxa de desocupação, índice PMC e população...")
    df_ibge = ibge.coletar(data_corte=DATA_CORTE)
    caminho_ibge = SAIDA / f"ibge_corte-{DATA_CORTE}_run-{timestamp}.parquet"
    df_ibge.to_parquet(caminho_ibge, index=False)
    print(f"  {len(df_ibge)} linhas, variáveis: {sorted(df_ibge['variavel'].unique())}")
    print(f"  salvo em {caminho_ibge}")

    if os.environ.get("PORTAL_TRANSPARENCIA_TOKEN"):
        print(
            "\n[Portal da Transparência] token encontrado, mas esta fonte é por "
            "município (sem agregado nacional/UF) — rodar separadamente com a "
            "lista de códigos IBGE de interesse, ver src/data/transparencia.py."
        )
    else:
        print(
            "\n[Portal da Transparência] PORTAL_TRANSPARENCIA_TOKEN não configurado "
            "— fonte pulada. Cadastre um e-mail em "
            "https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email "
            "para obter um token gratuito."
        )

    print(
        "\nFontes ainda pendentes (sem API oficial estável, exigem arquivo de "
        "exportação manual em data/raw/<fonte>/ — ver docstring de cada módulo "
        "em src/data/): PEIC, EPAE, painéis SPA/MF, Google Trends, ESTBAN."
    )


if __name__ == "__main__":
    main()
