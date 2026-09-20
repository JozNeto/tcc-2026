# Spec — 04. Avaliação, Métricas e Harness de Regressão

> Fornece a infraestrutura de métricas e comparação usada por `specs/03-modelagem` e
> pelo harness de testes em `tests/model_eval_harness/`. Não redefine modelos —
> define como eles são julgados.

## Objetivo

Centralizar a definição das métricas de erro, dos testes estatísticos de comparação
de desempenho, e do mecanismo que impede regressão de performance entre execuções do
pipeline (constitution §6 e §9).

## Escopo

1. **Métricas** (`src/evaluation/metricas.py`): implementação (ou wrapper documentado
   sobre biblioteca de terceiros) de erro relativo — MASE e/ou sMAPE, decisão
   registrada em ADR — além de RMSE/MAE para leitura complementar.
2. **Teste estatístico de diferença de desempenho** (`src/evaluation/testes_estatisticos.py`):
   ex. teste de Diebold-Mariano entre pares de modelos, com correção para múltiplas
   comparações se mais de dois modelos forem comparados simultaneamente.
3. **Harness de regressão** (`tests/model_eval_harness/`): compara a métrica do
   modelo campeão da execução atual contra a última execução registrada em
   `tests/model_eval_harness/historico_metricas.jsonl`, falhando se a piora exceder o
   limiar de `tests/model_eval_harness/limiares.py`.
4. **Validação do indicador territorial** (`src/evaluation/validacao_territorial.py`):
   já que o indicador composto (Recorte 1) não tem estatística oficial para comparar
   diretamente (constitution §5), este módulo implementa checagens de sanidade
   indiretas (ex.: correlação com proxies conhecidos, estabilidade a pequenas
   mudanças de peso) — não valida contra "verdade", documenta plausibilidade.

## Critérios de aceite (Definition of Done)

1. `metricas.py` tem teste unitário com valores calculados à mão para uma série
   sintética pequena (≤ 10 pontos), conferindo a fórmula exata usada.
2. `testes_estatisticos.py` tem teste unitário com dois vetores de erro sintéticos
   onde a significância esperada é conhecida (ex.: um caso claramente significativo,
   um caso claramente não significativo).
3. O harness de regressão roda via `make test` (sem flag de rede) e:
   - Na primeira execução (sem histórico), grava a métrica atual como baseline e
     passa.
   - Nas execuções seguintes, compara contra o último registro e falha com mensagem
     explícita (`métrica X piorou de A para B, limiar é C`) se exceder o limiar.
4. `validacao_territorial.py` documenta explicitamente, no docstring do módulo, que
   suas checagens são de plausibilidade e não de acurácia — evitando que o indicador
   composto seja lido como validado estatisticamente (risco de má interpretação
   citado na proposta, seção 8).

## Contrato de dados

**Entrada:** saídas de `specs/03-modelagem` (`data/processed/previsoes/*.parquet`)
mais a série real observada equivalente (do output de `specs/02-limpeza-eda`).

**Saída (`tests/model_eval_harness/historico_metricas.jsonl`):** uma linha JSON por
execução: `{"timestamp", "modelo", "serie", "metrica", "valor", "versao_base_usada", "seed"}`.

## Casos de borda

- Métrica indefinida (ex.: MASE quando a série de treino é constante — denominador
  zero): módulo deve levantar erro explícito, não retornar `NaN` silencioso que possa
  ser confundido com métrica válida.
- Limiar de regressão muito apertado gerando falso positivo por ruído de reamostragem
  do rolling origin: limiar deve ter margem documentada e justificada em ADR, não um
  número arbitrário.

## Fora de escopo

- Definição dos modelos em si → `specs/03-modelagem`.
- Apresentação dos resultados na monografia/dashboard → `specs/05-relatorio-entrega`.
