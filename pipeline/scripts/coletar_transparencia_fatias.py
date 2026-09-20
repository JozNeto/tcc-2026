"""Uma fatia da coleta do Novo Bolsa Família por município (retomável).

Uso: python scripts/coletar_transparencia_fatias.py [--mes 202512] [--fatia 150] [--pausa 1.5]

Cada execução consulta no máximo --fatia municípios e para. Rode de novo para
continuar de onde parou. Para no primeiro HTTP 429/403 sem insistir.
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
    args = ap.parse_args()

    _carregar_env()
    pasta = RAIZ / "data" / "raw" / "transparencia"
    municipios = tf.listar_municipios_ibge(cache=pasta / "municipios_ibge.csv")
    arq = pasta / f"bolsa_familia_{args.mes}.csv"

    r = tf.coletar_fatia(municipios, args.mes, arq, args.fatia, args.pausa)
    print(f"Fatia: {r['coletados_nesta_execucao']} municípios | "
          f"progresso: {r['total_feitos']}/{r['total_municipios']}")
    if r["parou_por_limite"]:
        print("A API sinalizou limite de uso — parei. Aguarde alguns minutos e rode de novo.")
    elif r["total_feitos"] < r["total_municipios"]:
        print("Rode novamente para a próxima fatia.")
    else:
        print("Coleta completa. Agregado por UF:")
        print(tf.agregar_por_uf(arq).to_string(index=False))


if __name__ == "__main__":
    main()
