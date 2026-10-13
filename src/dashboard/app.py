"""Painel interativo de consulta aos resultados.

**Este app não calcula nada.** Só lê `data/processed/` e plota — toda lógica de
indicador/modelo vive em `src/features/` e `src/models/`. Rodar com `make dashboard` ou `streamlit run src/dashboard/app.py`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DIRETORIO_PROCESSADO = Path("data/processed")


def listar_bases_disponiveis(diretorio: Path) -> list[Path]:
    if not diretorio.exists():
        return []
    return sorted(diretorio.glob("*.parquet"))


def montar_pagina() -> None:
    st.set_page_config(page_title="Apostas online e vulnerabilidade financeira", layout="wide")
    st.title("Apostas online e vulnerabilidade financeira das famílias brasileiras")
    st.caption(
        "Painel de consulta aos resultados — TCC Ciência de Dados (UNIVESP). "
        "Indicadores territoriais (por UF/município) são aproximações exploratórias, "
        "não medição oficial."
    )

    bases = listar_bases_disponiveis(DIRETORIO_PROCESSADO)

    if not bases:
        st.warning(
            "Nenhuma base processada encontrada em `data/processed/`. Rode o pipeline "
            "de coleta e tratamento (`src/data/`, `src/features/`) antes de usar este "
            "painel."
        )
        return

    caminho_selecionado = st.selectbox("Base processada", bases, format_func=lambda p: p.name)
    base = pd.read_parquet(caminho_selecionado)

    st.dataframe(base, use_container_width=True)

    colunas_numericas = base.select_dtypes("number").columns.tolist()
    if colunas_numericas:
        coluna = st.selectbox("Variável", colunas_numericas)
        st.line_chart(base[coluna])
    else:
        st.info("Nenhuma coluna numérica encontrada nesta base para plotar.")


montar_pagina()
