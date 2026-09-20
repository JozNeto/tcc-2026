#!/usr/bin/env bash
# Roda fatias da coleta do Bolsa Família em sequência, com pausa entre elas.
# Para na primeira sinalização de limite de uso da API, quando a coleta terminar,
# ou após 3 falhas seguidas (falhas isoladas, como queda de rede, são toleradas:
# espera e tenta a mesma fatia de novo — o progresso já gravado nunca se perde).
# Uso: bash scripts/rodar_fatias_em_sequencia.sh [mes] [fatia] [pausa_entre_fatias_s]
set -u
cd "$(dirname "$0")/.."
MES="${1:-202512}"
FATIA="${2:-150}"
PAUSA_FATIAS="${3:-180}"
PAUSA_REQ="${4:-1.5}"
falhas=0

while true; do
  saida=$(.venv/bin/python scripts/coletar_transparencia_fatias.py --mes "$MES" --fatia "$FATIA" --pausa "$PAUSA_REQ" 2>&1)
  rc=$?
  echo "[$(date -u +%FT%TZ)] rc=$rc"
  echo "$saida" | tail -5
  if echo "$saida" | grep -q "limite de uso"; then echo "LIMITE sinalizado — parando."; exit 2; fi
  if [ $rc -ne 0 ]; then
    falhas=$((falhas+1))
    if [ $falhas -ge 3 ]; then echo "3 falhas seguidas — parando."; exit $rc; fi
    echo "falha $falhas/3 — aguardando 5 min e tentando de novo."
    sleep 300
    continue
  fi
  falhas=0
  if echo "$saida" | grep -q "Coleta completa"; then echo "$saida"; echo "CONCLUÍDO."; exit 0; fi
  sleep "$PAUSA_FATIAS"
done
