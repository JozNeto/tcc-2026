"""Análise da pergunta central: há sinais de prejuízo à renda das famílias mais pobres
associados a jogos e apostas online?

CRITÉRIOS DEFINIDOS ANTES DE VER OS RESULTADOS (nada aqui prova causalidade):
  C1 (série temporal nacional, 2020–2025): o interesse de busca por apostas ("apostas online")
     está positivamente associado a variações posteriores (defasagem 0–6 meses) da
     inadimplência PF total ou do cartão rotativo, controlando Selic, desocupação e
     rendimento real, com p-valor ajustado por Bonferroni < 0,05.
  C2 (corte transversal, 27 UFs): interesse de busca por apostas é maior nas UFs mais
     dependentes do Bolsa Família per capita ou de menor rendimento (Spearman, Bonferroni).
  C3 (descritivo): quebras estruturais das séries de crédito próximas aos marcos de 2025.
Saídas: data/processed/resultados_pergunta_central.json, reports/figures/*.png e
data/processed/tabelas_pergunta_central.md.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.features import associacao as ass
from src.features.quebras_estruturais import (
    confrontar_com_calendario_regulatorio,
    detectar_quebras,
)

RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
FIG = RAIZ / "reports" / "figures"
JANELA = (dt.date(2020, 1, 1), dt.date(2025, 12, 1))
TERMO_PRINCIPAL = "apostas online"
TERMOS = ["apostas online", "bet", "jogo do tigrinho"]
Y_CREDITO = ["inadimplencia_pf_total", "inadimplencia_cartao_rotativo", "comprometimento_renda_pf", "endividamento_familias_sfn"]
CONTROLES = ["selic_acumulada_mes_anualizada", "taxa_desocupacao", "rendimento_medio_real_habitual"]


def _mensal() -> pd.DataFrame:
    base = pd.concat([pd.read_parquet(RAW / "analise_central" / "sgs.parquet"),
                      pd.read_parquet(RAW / "analise_central" / "ibge_nacional.parquet")])
    base["data_referencia"] = pd.to_datetime(base["data_referencia"])
    wide = base.pivot_table(index="data_referencia", columns="variavel", values="valor", aggfunc="first")
    tr = pd.read_parquet(RAW / "analise_central" / "trends_temporal.parquet")
    tr["data_referencia"] = pd.to_datetime(tr["data_referencia"])
    tr = tr.pivot_table(index="data_referencia", columns="termo", values="valor")
    tr.columns = [f"trends__{c}" for c in tr.columns]
    df = wide.join(tr, how="inner")
    return df.loc[pd.Timestamp(JANELA[0]):pd.Timestamp(JANELA[1])]


def analise_temporal(df: pd.DataFrame) -> dict:
    saida: dict = {}
    for termo in TERMOS:
        x = df[f"trends__{termo}"]
        linhas = []
        for y_nome in Y_CREDITO:
            for lag in range(7):
                r = ass.regressao_defasada_hac(df[y_nome], x, df[CONTROLES], lag)
                r.update({"y": y_nome, "termo": termo})
                linhas.append(r)
        adj = ass.bonferroni([r["p_valor"] for r in linhas])
        for r, p in zip(linhas, adj, strict=True):
            r["p_ajustado"] = p
        gr = {y: ass.granger(df[y_nome := y], x, 6) for y in Y_CREDITO}
        adj_g = ass.bonferroni([g["menor_p"] for g in gr.values()])
        for (y, g), p in zip(gr.items(), adj_g, strict=True):
            g["p_ajustado"] = p
        saida[termo] = {"regressoes": linhas, "granger": gr}
    return saida


def analise_uf() -> tuple[pd.DataFrame, dict]:
    reg = pd.read_parquet(RAW / "analise_central" / "trends_regional.parquet")
    trends = reg.pivot_table(index="uf", columns="termo", values="valor")
    composto = trends.apply(ass.normalizar_min_max).mean(axis=1).rename("trends_composto")
    pop = pd.read_parquet(RAW / "analise_central" / "uf_populacao_2025.parquet").set_index("uf")["valor"]
    rend = pd.read_parquet(RAW / "analise_central" / "uf_rendimento_2025T4.parquet").set_index("uf")["valor"]
    bf = pd.read_csv(PROC / "bolsa_familia_por_uf_202512.csv").set_index("uf")
    uf = pd.DataFrame({"trends_composto": composto, "rendimento_pnad": rend,
                       "bf_per_capita": bf["valor_repassado"] / pop,
                       "bf_familias_por_100hab": bf["beneficiarios"] / pop * 100})
    uf = uf.join(trends.add_prefix("trends__"))
    testes = []
    for ind in ["trends_composto"] + [f"trends__{t}" for t in TERMOS]:
        for cov in ["bf_per_capita", "rendimento_pnad"]:
            r = ass.spearman(uf[ind], uf[cov])
            r.update({"indicador": ind, "covariavel": cov})
            testes.append(r)
    for r, p in zip(testes, ass.bonferroni([t["p_valor"] for t in testes]), strict=True):
        r["p_ajustado"] = p
    return uf, {"testes": testes}


def quebras(df: pd.DataFrame) -> dict:
    saida = {}
    for nome in Y_CREDITO + [f"trends__{TERMO_PRINCIPAL}"]:
        s = df[nome].dropna()
        pen = float(np.var(s.to_numpy())) * float(np.log(len(s)))
        qs = detectar_quebras(s.set_axis(s.index.date), penalidade=pen, modelo="l2")
        conf = confrontar_com_calendario_regulatorio(qs, tolerancia_dias=45)
        saida[nome] = {"quebras": [str(q) for q in qs],
                       "coincidem_com_marcos": conf.loc[conf["coincide_dentro_da_tolerancia"], "marco"].tolist()}
    return saida


def dimensionamento(df: pd.DataFrame) -> dict:
    ggr, cpfs = 36959783379.70, 25245319
    bf = pd.read_csv(RAW / "transparencia" / "bolsa_familia_202512.csv")
    beneficio_medio = float(bf["valor"].sum() / bf["beneficiarios"].sum())
    rend = float(df["rendimento_medio_real_habitual"].iloc[-1])
    ggr_mensal = ggr / cpfs / 12
    return {
        "ggr_2025_por_cpf_unico_ano": ggr / cpfs,
        "ggr_2025_por_cpf_unico_mes": ggr_mensal,
        "beneficio_bolsa_familia_medio_dez2025": beneficio_medio,
        "rendimento_medio_real_habitual_dez2025": rend,
        "razao_ggr_mensal_sobre_beneficio_bf": ggr_mensal / beneficio_medio,
        "razao_ggr_mensal_sobre_rendimento": ggr_mensal / rend,
    }


def figuras(df: pd.DataFrame, uf: pd.DataFrame) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    for nome, rot in [(f"trends__{TERMO_PRINCIPAL}", "Interesse de busca: apostas online"),
                      ("inadimplencia_pf_total", "Inadimplência PF total (%)"),
                      ("inadimplencia_cartao_rotativo", "Inadimplência cartão rotativo (%)")]:
        ax.plot(df.index, ass.normalizar_min_max(df[nome]), label=rot)
    for d, r in [("2025-01-01", "Regulamentação"), ("2025-10-01", "Restrição Bolsa Família")]:
        ax.axvline(pd.Timestamp(d), color="gray", linestyle="--", linewidth=0.8)
        ax.text(pd.Timestamp(d) - pd.Timedelta(days=25), 0.55, r, fontsize=7, rotation=90, va="bottom", ha="right")
    ax.set_title("Séries normalizadas (mín–máx), 2020–2025")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "fig1_series_temporais.png", bbox_inches="tight", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(uf["bf_per_capita"], uf["trends_composto"])
    for sigla, linha in uf.iterrows():
        ax.annotate(sigla, (linha["bf_per_capita"], linha["trends_composto"]), fontsize=7)
    ax.set_xlabel("Bolsa Família per capita, dez/2025 (R$)")
    ax.set_ylabel("Interesse de busca composto (0–1)")
    ax.set_title("27 UFs: dependência de transferências × interesse por apostas")
    fig.savefig(FIG / "fig2_uf_dispersao.png", bbox_inches="tight", dpi=150)
    plt.close(fig)


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    df = _mensal()
    print(f"Janela mensal: {df.index.min().date()} a {df.index.max().date()} ({len(df)} meses)")
    temporal = analise_temporal(df)
    uf, transversal = analise_uf()
    res = {
        "janela": [str(JANELA[0]), str(JANELA[1])],
        "n_meses": len(df),
        "temporal": temporal,
        "transversal": transversal,
        "quebras": quebras(df),
        "dimensionamento": dimensionamento(df),
        "ranking_uf_trends_composto": uf["trends_composto"].sort_values(ascending=False).round(3).to_dict(),
    }
    (PROC / "resultados_pergunta_central.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    uf.round(3).to_csv(PROC / "uf_indicadores_pergunta_central.csv")
    figuras(df, uf)

    t = temporal[TERMO_PRINCIPAL]["regressoes"]
    c1 = [r for r in t if r["y"] in ("inadimplencia_pf_total", "inadimplencia_cartao_rotativo")
          and r["p_ajustado"] < 0.05 and r["coef_por_desvio_padrao"] > 0]
    c2 = [x for x in transversal["testes"] if x["indicador"] == "trends__apostas online"
          and x["p_ajustado"] < 0.05 and ((x["covariavel"] == "bf_per_capita" and x["rho"] > 0)
                                          or (x["covariavel"] == "rendimento_pnad" and x["rho"] < 0))]
    c3 = [k for k, v in res["quebras"].items() if v["coincidem_com_marcos"]]
    res["veredito_criterios"] = {"C1_atendido": bool(c1), "C1_detalhe": c1, "C2_atendido": bool(c2),
                                 "C3_series_com_quebra_em_marco_2025": c3}
    (PROC / "resultados_pergunta_central.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nVEREDITO -> C1:", bool(c1), "| C2:", bool(c2), "| C3:", c3)
    print("\n== C1 temporal (termo principal): melhores associações ==")
    reg = pd.DataFrame(temporal[TERMO_PRINCIPAL]["regressoes"]).sort_values("p_valor").head(6)
    print(reg[["y", "defasagem", "coef_por_desvio_padrao", "delta_r2", "p_hac", "p_ols", "p_ajustado", "n"]].round(4).to_string(index=False))
    print("Granger:", {y: (round(g["menor_p"], 4), round(g["p_ajustado"], 4)) for y, g in temporal[TERMO_PRINCIPAL]["granger"].items()})
    print("\n== C2 corte transversal ==")
    print(pd.DataFrame(transversal["testes"])[["indicador", "covariavel", "rho", "p_valor", "p_ajustado", "n"]].round(4).to_string(index=False))
    print("\n== C3 quebras ==")
    for k, v in res["quebras"].items():
        print(k, v)
    print("\n== Dimensionamento ==")
    for k, v in res["dimensionamento"].items():
        print(f"{k}: {v:,.4f}")
    print("\n== Ranking UF (interesse composto) top 8 ==")
    print(uf["trends_composto"].sort_values(ascending=False).head(8).round(3).to_string())


if __name__ == "__main__":
    main()
