"""Projeção univariada das séries de crédito das famílias (24 meses) com validação por origem móvel.

IMPORTANTE (declarar na monografia): esta projeção extrapola a dinâmica da própria série. NÃO é
condicionada à exposição a apostas — a análise de associação (analisar_pergunta_central.py) não
encontrou relação temporal que a sustentasse. Serve para mostrar a trajetória esperada do crédito
"mantido o padrão recente", com intervalos de predição de 95%.

Protocolo (definido antes de rodar): histórico completo do SGS até 31/12/2025; modelos naive,
naive sazonal (12) e três especificações de SARIMAX sem exógena; origem móvel com horizonte de 12
meses e passo de 1 mês, treino mínimo de 60% da série; métrica MASE; teste de Diebold-Mariano
(SARIMAX x naive) em h=1 e h=12; cobertura empírica do intervalo de 95% em h=12. O modelo usado na
projeção é o de menor MASE em h=12.

Saídas: data/processed/projecao_credito.json e projecao_credito.csv; reports/figures/fig3_projecao.png
Uso: python scripts/projetar_credito.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.evaluation.metricas import calcular_mase
from src.evaluation.testes_estatisticos import (
    EstatisticaError,
    calcular_diebold_mariano,
)
from src.models.baseline import NaiveModel, SeasonalNaiveModel
from src.models.econometricos import SARIMAXModel
from src.models.validacao import validar_rolling_origin

warnings.filterwarnings("ignore")

SERIES = {
    "inadimplencia_pf_total": "Inadimplência PF total (%)",
    "inadimplencia_cartao_rotativo": "Inadimplência do cartão rotativo (%)",
    "comprometimento_renda_pf": "Comprometimento de renda (%)",
    "endividamento_familias_sfn": "Endividamento das famílias (% da renda)",
}
MODELOS = {
    "naive": lambda: NaiveModel(),
    "naive_sazonal": lambda: SeasonalNaiveModel(12),
    "sarimax_110": lambda: SARIMAXModel(order=(1, 1, 0)),
    "sarimax_011": lambda: SARIMAXModel(order=(0, 1, 1)),
    "sarimax_111": lambda: SARIMAXModel(order=(1, 1, 1)),
}
H_VAL, H_PROJ, FRAC_TREINO = 12, 24, 0.6


def carregar() -> dict[str, pd.Series]:
    base = pd.read_parquet(RAIZ / "data" / "raw" / "analise_central" / "sgs.parquet")
    base["data_referencia"] = pd.to_datetime(base["data_referencia"]).dt.date
    out = {}
    for k in SERIES:
        s = base[base["variavel"] == k].sort_values("data_referencia").set_index("data_referencia")["valor"]
        out[k] = s.astype(float)
    return out


def avaliar(serie: pd.Series) -> tuple[dict, dict]:
    n_min = int(len(serie) * FRAC_TREINO)
    treino0 = serie.iloc[:n_min]
    resultados, erros = {}, {}
    for nome, fabrica in MODELOS.items():
        v = validar_rolling_origin(serie, fabrica, tamanho_minimo_treino=n_min, horizonte=H_VAL, passo=1)
        v["passo"] = v.groupby("origem").cumcount() + 1
        v["erro"] = v["valor_real"] - v["previsao"]
        erros[nome] = v
        r = {}
        for h in (1, H_VAL):
            vh = v[v["passo"] == h]
            r[f"mase_h{h}"] = calcular_mase(vh["valor_real"], vh["previsao"], treino0)
        vh = v[v["passo"] == H_VAL]
        r["cobertura95_h12"] = float(((vh["valor_real"] >= vh["intervalo_inferior"])
                                      & (vh["valor_real"] <= vh["intervalo_superior"])).mean())
        r["n_origens"] = int(v["origem"].nunique())
        resultados[nome] = r
    for nome in MODELOS:
        for h in (1, H_VAL):
            if nome == "naive":
                continue
            a = erros[nome][erros[nome]["passo"] == h].set_index("origem")["erro"]
            b = erros["naive"][erros["naive"]["passo"] == h].set_index("origem")["erro"]
            idx = a.index.intersection(b.index)
            try:
                dm = calcular_diebold_mariano(a.loc[idx], b.loc[idx], h=h)
                resultados[nome][f"dm_p_h{h}"] = dm["p_valor"]
                resultados[nome][f"melhor_que_naive_h{h}"] = bool(dm["modelo_1_melhor"])
            except EstatisticaError:
                resultados[nome][f"dm_p_h{h}"] = None
                resultados[nome][f"melhor_que_naive_h{h}"] = None
    return resultados, erros


def main() -> None:
    dados = carregar()
    saida, tabelas, fig_dados = {}, [], {}
    for chave, rotulo in SERIES.items():
        serie = dados[chave]
        print(f"\n== {rotulo}: {len(serie)} obs ({serie.index[0]} a {serie.index[-1]}) ==")
        res, _ = avaliar(serie)
        melhor = min(res, key=lambda m: res[m]["mase_h12"])
        print(pd.DataFrame(res).T[["mase_h1", "mase_h12", "cobertura95_h12", "dm_p_h12", "melhor_que_naive_h12"]].round(3))
        print("melhor (MASE h=12):", melhor)

        modelo = MODELOS[melhor]().fit(serie)
        prev = modelo.predict(H_PROJ)
        prev["serie"], prev["modelo"] = chave, melhor
        tabelas.append(prev)
        fig_dados[chave] = (serie, prev)
        saida[chave] = {"rotulo": rotulo, "n_obs": len(serie), "inicio": str(serie.index[0]),
                        "fim": str(serie.index[-1]), "modelos": res, "modelo_escolhido": melhor,
                        "projecao_dez2027": {k: float(prev[k].iloc[-1]) for k in
                                             ("previsao", "intervalo_inferior", "intervalo_superior")},
                        "ultimo_valor": float(serie.iloc[-1])}

    proc = RAIZ / "data" / "processed"
    (proc / "projecao_credito.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.concat(tabelas).to_csv(proc / "projecao_credito.csv", index=False)

    fig, eixos = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (chave, (serie, prev)) in zip(eixos.ravel(), fig_dados.items(), strict=True):
        hist = serie.iloc[-84:]
        ax.plot(pd.to_datetime(hist.index), hist.to_numpy(), color="tab:gray", label="Observado")
        d = pd.to_datetime(prev["data_referencia"])
        ax.plot(d, prev["previsao"], color="tab:blue", label="Projeção")
        ax.fill_between(d, prev["intervalo_inferior"], prev["intervalo_superior"], alpha=0.2, color="tab:blue",
                        label="Intervalo de 95%")
        esc = saida[chave]["modelo_escolhido"]
        rot_mod = {"sarimax_110": "SARIMAX(1,1,0)", "sarimax_011": "SARIMAX(0,1,1)",
                   "sarimax_111": "SARIMAX(1,1,1)"}.get(esc, esc)
        ax.set_title(f"{SERIES[chave]}\n{rot_mod}", fontsize=9)
        ax.tick_params(labelsize=8)
    eixos[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(RAIZ / "reports" / "figures" / "fig3_projecao.png", dpi=150)
    print("\nSalvo em", proc / "projecao_credito.json")


if __name__ == "__main__":
    main()
