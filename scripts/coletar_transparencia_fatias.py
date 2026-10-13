"""Uma fatia da coleta do Novo Bolsa Família por município (retomável).

Uso: python scripts/coletar_transparencia_fatias.py [--mes 202512] [--fatia 150] [--pausa 1.5]
     [--ufs AP,RR] [--saida CAMINHO] [--saida-agregado CAMINHO]

Cada execução consulta no máximo --fatia municípios e para. Rode de novo para
continuar de onde parou. Para no primeiro HTTP 429/403 sem insistir.

--ufs restringe a coleta a UFs específicas (separadas por vírgula) — útil para
testar/validar a pipeline (ex.: no workflow do GitHub Actions) sem rodar os 5.571
municípios nem tocar nos dados reais. Nesse modo, por padrão, a saída vai para
data/processed/bolsa-familia-coleta-parcial/<UFs>.csv (agregado) e
<UFs>_bruto.csv (bruto por município) — não para os caminhos normais
(data/raw/transparencia/bolsa_familia_<mes>.csv e
data/processed/bolsa_familia_por_uf_<mes>.csv). --saida e --saida-agregado
sobrescrevem esses caminhos, se precisar de outro lugar.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.data import transparencia_fatias as tf


def _carregar_env() -> None:
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text().splitlines():
            if "=" in linha and not linha.startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes", default="202512")
    ap.add_argument("--fatia", type=int, default=150)
    ap.add_argument("--pausa", type=float, default=1.5)
    ap.add_argument("--ufs", default=None, help="UFs separadas por vírgula, para coleta parcial (teste). Ex.: AP,RR")
    ap.add_argument("--saida", default=None, help="Caminho do CSV de progresso bruto (sobrescreve o padrão)")
    ap.add_argument("--saida-agregado", default=None, help="Caminho do CSV agregado por UF (sobrescreve o padrão)")
    args = ap.parse_args()

    _carregar_env()
    pasta = RAIZ / "data" / "raw" / "transparencia"
    municipios = tf.listar_municipios_ibge(cache=pasta / "municipios_ibge.csv")

    ufs_slug = None
    if args.ufs:
        ufs = {u.strip().upper() for u in args.ufs.split(",") if u.strip()}
        municipios = municipios[municipios["uf"].isin(ufs)].reset_index(drop=True)
        if municipios.empty:
            raise SystemExit(f"nenhum município encontrado para as UFs {sorted(ufs)!r}")
        ufs_slug = "-".join(sorted(ufs))
        print(f"Coleta parcial (teste): restrita a {sorted(ufs)} ({len(municipios)} municípios).")

    pasta_parcial = RAIZ / "data" / "processed" / "bolsa-familia-coleta-parcial"
    arq = Path(args.saida) if args.saida else (
        pasta_parcial / f"{ufs_slug}_bruto.csv" if ufs_slug else pasta / f"bolsa_familia_{args.mes}.csv"
    )
    if not arq.is_absolute():
        arq = RAIZ / arq
    arq.parent.mkdir(parents=True, exist_ok=True)

    r = tf.coletar_fatia(municipios, args.mes, arq, args.fatia, args.pausa)
    print(f"Fatia: {r['coletados_nesta_execucao']} municípios | "
          f"progresso: {r['total_feitos']}/{r['total_municipios']}")
    if r["parou_por_limite"]:
        print("A API sinalizou limite de uso — parei. Aguarde alguns minutos e rode de novo.")
    elif r["total_feitos"] < r["total_municipios"]:
        print("Rode novamente para a próxima fatia.")
    else:
        agregado = tf.agregar_por_uf(arq)
        saida = Path(args.saida_agregado) if args.saida_agregado else (
            pasta_parcial / f"{ufs_slug}.csv" if ufs_slug
            else RAIZ / "data" / "processed" / f"bolsa_familia_por_uf_{args.mes}.csv"
        )
        if not saida.is_absolute():
            saida = RAIZ / saida
        saida.parent.mkdir(parents=True, exist_ok=True)
        agregado.to_csv(saida, index=False)
        print("Coleta completa. Agregado por UF salvo em", saida)
        print(agregado.to_string(index=False))
        if not args.ufs:
            print(
                "\nEsse arquivo é a única exceção versionada em data/processed/ (ver .gitignore) — "
                "é usado por scripts/analisar_pergunta_central.py e é caro de refazer. Depois de "
                "gerá-lo, faça commit dele (veja o README, seção 'Dados versionados por exceção')."
            )


if __name__ == "__main__":
    main()
