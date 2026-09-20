"""Harness de regressão de performance entre execuções (specs/04-avaliacao/spec.md).

Compara a métrica do modelo campeão da execução atual contra o último registro
salvo em `historico_metricas.jsonl` para o mesmo (modelo, série, métrica). Na
primeira execução (sem histórico), grava a métrica atual como baseline e passa.

`src/models/` e `src/evaluation/` devem chamar `registrar_e_comparar` ao final de
cada rodada de comparação de modelos, sempre passando `metrica_menor_e_melhor`
explicitamente (nem toda métrica é "menor é melhor").
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from tests.model_eval_harness.limiares import LIMIAR_REGRESSAO_RELATIVA

HISTORICO_PATH = Path(__file__).resolve().parent / "historico_metricas.jsonl"


class RegressaoDeMetricaError(Exception):
    """Levantado quando a métrica do modelo campeão piora além do limiar tolerado."""


@dataclass(frozen=True)
class RegistroMetrica:
    timestamp: str
    modelo: str
    serie: str
    metrica: str
    valor: float
    versao_base_usada: str
    seed: int


def _ler_historico(caminho: Path) -> list[RegistroMetrica]:
    if not caminho.exists() or caminho.stat().st_size == 0:
        return []
    registros = []
    with caminho.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                registros.append(RegistroMetrica(**json.loads(linha)))
    return registros


def _gravar_registro(caminho: Path, registro: RegistroMetrica) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(registro)) + "\n")


def ultimo_registro(caminho: Path, modelo: str, serie: str, metrica: str) -> RegistroMetrica | None:
    correspondentes = [
        r
        for r in _ler_historico(caminho)
        if r.modelo == modelo and r.serie == serie and r.metrica == metrica
    ]
    return correspondentes[-1] if correspondentes else None


def registrar_e_comparar(
    *,
    modelo: str,
    serie: str,
    metrica: str,
    valor: float,
    versao_base_usada: str,
    seed: int,
    metrica_menor_e_melhor: bool = True,
    limiar: float = LIMIAR_REGRESSAO_RELATIVA,
    caminho_historico: Path = HISTORICO_PATH,
) -> None:
    """Registra a métrica atual e levanta RegressaoDeMetricaError se ela piorou além
    do limiar em relação ao último registro para o mesmo (modelo, serie, metrica)."""
    anterior = ultimo_registro(caminho_historico, modelo, serie, metrica)

    novo = RegistroMetrica(
        timestamp=datetime.now(timezone.utc).isoformat(),
        modelo=modelo,
        serie=serie,
        metrica=metrica,
        valor=valor,
        versao_base_usada=versao_base_usada,
        seed=seed,
    )

    if anterior is not None and anterior.valor != 0:
        piora_relativa = (
            (valor - anterior.valor) / abs(anterior.valor)
            if metrica_menor_e_melhor
            else (anterior.valor - valor) / abs(anterior.valor)
        )
        if piora_relativa > limiar:
            raise RegressaoDeMetricaError(
                f"{metrica} de '{modelo}' em '{serie}' piorou de {anterior.valor} para "
                f"{valor} ({piora_relativa:.1%}), limiar é {limiar:.1%}"
            )

    _gravar_registro(caminho_historico, novo)
