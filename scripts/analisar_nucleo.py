"""Análise real das séries do núcleo nacional já coletadas: tratamento,
diagnóstico exploratório e detecção de quebras estruturais.

Consome os arquivos mais recentes de data/raw/sgs_*.parquet e data/raw/ibge_*.parquet
(gerados por scripts/coletar_nucleo.py) — não inventa nem aproxima nenhum valor.

Escopo desta rodada: apenas as séries de endividamento/inadimplência/atividade
econômica já coletadas por API real (comprometimento de renda, endividamento das
famílias, inadimplência PF, taxa de desocupação, índice PMC). A correlação cruzada
com o indicador de exposição a apostas fica pendente até as fontes SPA/MF, PEIC e
EPAE serem obtidas (ver README) — sem elas, não há uma série de exposição a apostas
para cruzar.

Uso: `python scripts/analisar_nucleo.py`
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.features.diagnostico import diagnosticar
from src.features.quebras_estruturais import (
    confrontar_com_calendario_regulatorio,
    detectar_quebras,
)
from src.features.tratamento import tratar

RAIZ = Path(__file__).resolve().parent.parent
DATA_CORTE = dt.date(2025, 12, 31)
DATA_BASE_DEFLACAO = dt.date(2025, 12, 1)
SERIES_NUCLEO_ANALISADAS = [
    "comprometimento_renda_pf",
    "endividamento_familias_sfn",
    "inadimplencia_pf",
]


def _carregar_mais_recente(padrao: str) -> pd.DataFrame:
    arquivos = sorted(glob.glob(str(RAIZ / "data" / "raw" / padrao)))
    if not arquivos:
        raise FileNotFoundError(f"nenhum arquivo casando com '{padrao}' em data/raw/ — rode scripts/coletar_nucleo.py primeiro")
    caminho = arquivos[-1]
    print(f"Carregando {caminho}")
    return pd.read_parquet(caminho)


def main() -> None:
    base_sgs = _carregar_mais_recente("sgs_*.parquet")
    base_ibge = _carregar_mais_recente("ibge_*.parquet")
    base_long = pd.concat([base_sgs, base_ibge], ignore_index=True)
    base_long["data_referencia"] = pd.to_datetime(base_long["data_referencia"]).dt.date

    ipca = base_long[base_long["variavel"] == "ipca_variacao_mensal"][["data_referencia", "valor"]]

    print("\n=== Tratamento (deflacionamento, imputação, outliers) ===")
    tratada = tratar(
        base_long,
        ipca_variacao_mensal=ipca,
        data_base_deflacao=DATA_BASE_DEFLACAO,
        variaveis_monetarias=set(),  # nenhuma variável coletada até agora é monetária (R$)
    )
    print(f"Base tratada: {tratada.shape[0]} datas x {tratada.shape[1]} colunas")

    resultados: dict = {"data_corte": str(DATA_CORTE), "series_analisadas": {}}

    for variavel in SERIES_NUCLEO_ANALISADAS:
        print(f"\n=== Diagnóstico: {variavel} ===")
        serie = tratada[variavel].dropna()
        diagnostico = diagnosticar(serie)

        estac = diagnostico["estacionariedade"]
        print(
            f"ADF p-valor={estac['adf_p_valor']:.4f} "
            f"(rejeita raiz unitária a 5%: {estac['adf_rejeita_raiz_unitaria_5pct']}) | "
            f"KPSS p-valor={estac['kpss_p_valor']:.4f} "
            f"(rejeita estacionariedade a 5%: {estac['kpss_rejeita_estacionariedade_5pct']})"
        )
        print(f"Decomposição sazonal disponível: {diagnostico['decomposicao_disponivel']}")

        print(f"\n=== Quebras estruturais: {variavel} ===")
        # Penalidade BIC-like para custo L2 (Pelt): var(sinal) * log(n) — heurística
        # padrão da documentação do `ruptures` para escolher a penalidade sem
        # conhecimento prévio do número de quebras. Não força nenhum número
        # específico de quebras — o algoritmo decide livremente.
        import numpy as np

        penalidade = float(np.var(serie.to_numpy())) * float(np.log(len(serie)))
        quebras = detectar_quebras(serie, penalidade=penalidade, modelo="l2")
        print(f"Penalidade usada (var*log(n)): {penalidade:.4f}")
        print(f"Quebras detectadas: {quebras}")

        confronto = confrontar_com_calendario_regulatorio(quebras)
        print(confronto.to_string(index=False))

        resultados["series_analisadas"][variavel] = {
            "n_observacoes": int(estac["n_observacoes"]),
            "adf_p_valor": float(estac["adf_p_valor"]),
            "adf_rejeita_raiz_unitaria_5pct": bool(estac["adf_rejeita_raiz_unitaria_5pct"]),
            "kpss_p_valor": float(estac["kpss_p_valor"]),
            "quebras_detectadas": [str(d) for d in quebras],
            "confronto_calendario_regulatorio": confronto.assign(
                data_marco=lambda d: d["data_marco"].astype(str),
                quebra_mais_proxima=lambda d: d["quebra_mais_proxima"].astype(str),
            ).to_dict(orient="records"),
        }

    caminho_saida = RAIZ / "data" / "processed" / f"resultados_nucleo_corte-{DATA_CORTE}.json"
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados salvos em {caminho_saida}")


if __name__ == "__main__":
    main()
