"""Testes de sanidade da estrutura do projeto.

Servem de placeholder útil enquanto `src/` ainda não tem código de pipeline: garantem
que os documentos fundacionais (constitution, specs, TDD) existem e não foram
apagados/renomeados por engano. Conforme os módulos de `src/` forem implementados,
os testes reais de cada um (`tests/unit/test_<modulo>.py`) substituem a necessidade
destes em cobertura, mas estes continuam válidos como guarda de integridade da
documentação viva do projeto.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent


def test_documentos_fundacionais_existem():
    obrigatorios = [
        "docs/00-proposta-resumo.md",
        "docs/tdd.md",
        "docs/glossario.md",
        "docs/referencias.md",
        "docs/adr/0001-registro-inicial.md",
        "specs/constitution.md",
        "specs/01-ingestao-dados/spec.md",
        "specs/02-limpeza-eda/spec.md",
        "specs/03-modelagem/spec.md",
        "specs/04-avaliacao/spec.md",
        "specs/05-relatorio-entrega/spec.md",
        "TASKS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
    ]
    faltantes = [caminho for caminho in obrigatorios if not (RAIZ / caminho).exists()]
    assert not faltantes, f"documentos fundacionais ausentes: {faltantes}"


def test_constitution_declara_data_de_corte():
    texto = (RAIZ / "specs" / "constitution.md").read_text(encoding="utf-8")
    assert "31/12/2025" in texto


def test_constitution_proibe_split_aleatorio():
    texto = (RAIZ / "specs" / "constitution.md").read_text(encoding="utf-8")
    assert "rolling origin" in texto.lower() or "walk-forward" in texto.lower()


def test_skills_mcp_existem():
    esperadas = [
        "contexto-proposta",
        "validacao-dados",
        "eda",
        "modelagem",
        "avaliacao-metrica",
        "redacao-academica",
    ]
    faltantes = [
        nome for nome in esperadas if not (RAIZ / ".mcp" / "skills" / nome / "SKILL.md").exists()
    ]
    assert not faltantes, f"skills ausentes: {faltantes}"
