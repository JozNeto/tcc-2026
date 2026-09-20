# Spec — 03. Modelagem Preditiva e Projeção de Cenários

> Cobre as **Etapas 5 e 6** da proposta ("Modelagem preditiva comparativa" e
> "Projeção de cenários e custo patrimonial"). Aplica-se **apenas ao núcleo nacional**
> — constitution §5 proíbe modelagem/projeção nos Recortes 1 e 2 territoriais.

## Objetivo

Construir uma escada de modelos de previsão de séries temporais para os indicadores
nacionais de endividamento/inadimplência, comparar seu desempenho sob validação
temporal rigorosa, e projetar cenários de 24 meses com intervalos de predição
explícitos, incluindo simulação do custo de oportunidade patrimonial.

## Escopo

1. **Escada de modelos** (`src/models/`):
   - `baseline.py` — naive e seasonal naive (obrigatórios, constitution §6).
   - `econometricos.py` — modelos econométricos com variáveis exógenas (ex.:
     SARIMAX com a exposição a apostas como exógena).
   - `ml_series.py` — abordagens de aprendizado de máquina aplicáveis a séries
     únicas (ex.: gradient boosting sobre features de defasagem, sem vazamento).
2. **Validação** (`src/models/validacao.py`): rolling origin / walk-forward
   obrigatório (constitution §2). Nenhum modelo entra na comparação final sem passar
   por este módulo.
3. **Projeção de cenários** (`src/models/cenarios.py`): três cenários — inercial,
   contenção, expansão — horizonte de 24 meses, intervalos de predição explícitos.
4. **Simulação de custo patrimonial** (`src/models/custo_patrimonial.py`): simulação
   estocástica (ex.: Monte Carlo) do patrimônio contrafactual associado ao
   redirecionamento do gasto médio observado em apostas.

## Critérios de aceite (Definition of Done)

1. Todo modelo em `src/models/` implementa uma interface comum
   (`fit(serie_treino) -> Modelo`, `predict(horizonte) -> DataFrame` com colunas
   `data_referencia`, `previsao`, `intervalo_inferior`, `intervalo_superior`), testável
   de forma intercambiável pelo harness de `tests/model_eval_harness/`.
2. `src/models/validacao.py` implementa rolling origin com parâmetros documentados
   (tamanho mínimo de janela de treino, passo do reajuste) e é usado por todos os
   modelos da escada — nenhum modelo é avaliado com split aleatório (constitution §2).
3. A comparação final de modelos reporta, por modelo: métrica de erro relativo (ex.:
   MASE ou sMAPE, a decidir em ADR) **e** resultado de teste estatístico de diferença
   de desempenho (ex.: Diebold-Mariano) contra o melhor baseline — ambos obrigatórios
   (constitution §6), nenhum modelo é declarado "melhor" sem o teste.
4. Todo cenário projetado inclui intervalo de predição explícito; o cenário inercial é
   rotulado programaticamente (campo `condicional_a_regulacao_estavel: True`) em todo
   output que o utiliza — não apenas em texto do relatório.
5. Horizontes além de 24 meses (se produzidos) carregam campo/rótulo
   `tipo: "exercicio_de_cenario"`, nunca `tipo: "previsao"`.
6. Seeds fixas em toda simulação estocástica; teste unitário garante que duas execuções
   com a mesma seed produzem resultado idêntico.
7. Teste unitário de regressão (`tests/model_eval_harness/`) falha o build se a métrica
   de erro do melhor modelo piorar além do limiar definido em
   `tests/model_eval_harness/limiares.py` em relação à última execução registrada.

## Contrato de dados

**Entrada:** base tratada de `specs/02-limpeza-eda`
(`data/processed/base_nacional_corte-*.parquet`).

**Saída de modelos** (`data/processed/previsoes/<modelo>_<serie>.parquet`): colunas
`data_referencia`, `previsao`, `intervalo_inferior`, `intervalo_superior`, `modelo`,
`seed`, `versao_base_usada`.

**Saída de cenários** (`data/processed/cenarios/<cenario>_<serie>.parquet`): mesmas
colunas + `cenario` (`inercial`/`contencao`/`expansao`) e
`condicional_a_regulacao_estavel: bool`.

## Casos de borda

- Série com quebra estrutural detectada perto do fim da amostra: documentar explicitamente
  se o modelo foi treinado incluindo ou excluindo o período pós-quebra, e por quê — não é
  uma decisão automática silenciosa.
- Variável exógena (exposição a apostas) com histórico mais curto que a variável-resposta
  (endividamento): modelos econométricos com exógena só podem usar o período em que ambas
  existem; documentar a perda de amostra resultante.
- Se nenhum modelo superar o baseline com significância estatística: isso é reportado como
  resultado válido, não descartado ou "forçado" via ajuste de hiperparâmetros até passar.

## Fora de escopo

- Métricas de avaliação detalhadas e harness de comparação entre execuções →
  `specs/04-avaliacao` (este spec consome esse harness, não o define).
- Redação dos resultados na monografia → `specs/05-relatorio-entrega`.
