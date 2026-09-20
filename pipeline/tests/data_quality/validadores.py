"""Validadores reutilizáveis de qualidade de dados.

Implementa o checklist de validação de dados
como funções puras e testáveis. Módulos de coleta (`src/data/`) e tratamento
(`src/features/`) devem chamar estas funções antes de gravar em `data/processed/`;
os testes deste diretório garantem que a lógica de validação em si está correta.

Cada validador levanta `ValidacaoDadosError` com uma lista de problemas encontrados,
em vez de retornar um booleano — a falha deve ser acionável.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

COLUNAS_LONG_FORMAT = ("data_referencia", "unidade", "variavel", "valor", "fonte", "coletado_em")


class ValidacaoDadosError(Exception):
    """Levantado quando uma ou mais checagens de qualidade falham."""


@dataclass
class RelatorioValidacao:
    """Resultado estruturado de uma rodada de validação — nunca um booleano isolado."""

    checagens_ok: list[str] = field(default_factory=list)
    checagens_falhas: list[str] = field(default_factory=list)

    @property
    def aprovado(self) -> bool:
        return not self.checagens_falhas

    def registrar(self, nome: str, ok: bool, detalhe: str = "") -> None:
        if ok:
            self.checagens_ok.append(nome)
        else:
            self.checagens_falhas.append(f"{nome}: {detalhe}" if detalhe else nome)

    def levantar_se_reprovado(self) -> None:
        if not self.aprovado:
            raise ValidacaoDadosError("; ".join(self.checagens_falhas))


def validar_schema(df: pd.DataFrame, colunas_esperadas: tuple[str, ...]) -> RelatorioValidacao:
    relatorio = RelatorioValidacao()
    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    relatorio.registrar(
        "schema_colunas_presentes", not faltantes, f"colunas faltantes: {faltantes}"
    )
    return relatorio


def validar_duplicatas(df: pd.DataFrame, chave: list[str]) -> RelatorioValidacao:
    relatorio = RelatorioValidacao()
    n_duplicadas = int(df.duplicated(subset=chave, keep=False).sum())
    relatorio.registrar(
        "sem_duplicatas_na_chave", n_duplicadas == 0, f"{n_duplicadas} linhas duplicadas em {chave}"
    )
    return relatorio


def validar_data_corte(
    df: pd.DataFrame, coluna_data: str, data_corte: date, permitir_dados_pos_corte: bool = False
) -> RelatorioValidacao:
    relatorio = RelatorioValidacao()
    if permitir_dados_pos_corte:
        relatorio.registrar("data_corte_respeitada", True, "checagem desativada explicitamente")
        return relatorio

    datas = pd.to_datetime(df[coluna_data]).dt.date
    além_do_corte = int((datas > data_corte).sum())
    relatorio.registrar(
        "data_corte_respeitada",
        além_do_corte == 0,
        f"{além_do_corte} linhas com {coluna_data} posterior a {data_corte}",
    )
    return relatorio


def validar_completude(df: pd.DataFrame, coluna: str, limite_ausencia: float = 0.5) -> RelatorioValidacao:
    """Sinaliza ausência acima de `limite_ausencia` (fração 0-1). Não decide se é
    falha estrutural esperada (ex.: série com início tardio) — isso é decisão de
    quem chama, documentada no docstring do módulo de coleta."""
    relatorio = RelatorioValidacao()
    fracao_ausente = float(df[coluna].isna().mean()) if len(df) else 1.0
    relatorio.registrar(
        "completude_dentro_do_limite",
        fracao_ausente <= limite_ausencia,
        f"{fracao_ausente:.1%} ausente em '{coluna}', limite é {limite_ausencia:.1%}",
    )
    return relatorio


def validar_range(
    df: pd.DataFrame, coluna: str, minimo: float | None = None, maximo: float | None = None
) -> RelatorioValidacao:
    relatorio = RelatorioValidacao()
    serie = df[coluna].dropna()
    if minimo is not None:
        abaixo = int((serie < minimo).sum())
        relatorio.registrar("range_minimo_respeitado", abaixo == 0, f"{abaixo} valores abaixo de {minimo}")
    if maximo is not None:
        acima = int((serie > maximo).sum())
        relatorio.registrar("range_maximo_respeitado", acima == 0, f"{acima} valores acima de {maximo}")
    return relatorio


def combinar(*relatorios: RelatorioValidacao) -> RelatorioValidacao:
    combinado = RelatorioValidacao()
    for r in relatorios:
        combinado.checagens_ok.extend(r.checagens_ok)
        combinado.checagens_falhas.extend(r.checagens_falhas)
    return combinado
