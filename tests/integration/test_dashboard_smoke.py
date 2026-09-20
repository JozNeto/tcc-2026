"""Teste de fumaça do dashboard Streamlit (spec 05, critério 1).

Roda o script do app em processo, via `streamlit.testing.v1.AppTest`, sem subir um
servidor HTTP de verdade. Marcado como integração (não `network`) porque depende de
`streamlit` estar instalado — roda em `make test`, já que não usa rede.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

CAMINHO_APP = str(Path(__file__).resolve().parent.parent.parent / "src" / "dashboard" / "app.py")


def test_dashboard_sobe_sem_erro_sem_dados_processados():
    """Sem nenhuma base em data/processed/, o app deve mostrar um aviso, não
    quebrar."""
    at = AppTest.from_file(CAMINHO_APP)
    at.run(timeout=30)

    assert not at.exception
    assert any("Nenhuma base processada" in aviso.value for aviso in at.warning)
