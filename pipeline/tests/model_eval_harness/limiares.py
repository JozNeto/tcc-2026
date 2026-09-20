"""Limiares de regressão de performance entre execuções.

Um limiar apertado demais gera falso positivo por ruído de reamostragem do rolling
origin. O valor abaixo é um ponto
de partida documentado, não definitivo — qualquer alteração deve vir acompanhada de
justificativa documentada para a nova margem.
"""

from __future__ import annotations

# Piora relativa máxima tolerada na métrica de erro do modelo campeão entre duas
# execuções consecutivas, antes do harness marcar como regressão. 0.05 = 5%.
LIMIAR_REGRESSAO_RELATIVA = 0.05
