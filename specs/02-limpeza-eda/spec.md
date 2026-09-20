# Spec — 02. Limpeza, EDA e Detecção de Quebras Estruturais

> Cobre as **Etapas 3 e 4** da proposta ("Tratamento e análise exploratória" e
> "Detecção de quebras estruturais"), além da construção do **indicador composto
> territorial** (parte descritiva da Etapa 7 — Recortes 1 e 2, sem modelagem/projeção,
> conforme `specs/constitution.md` §5).

## Objetivo

Transformar a saída bruta de `specs/01-ingestao-dados` em uma base nacional mensal
tratada, documentada e analisada exploratoriamente, e detectar quebras estruturais
nas séries financeiras nacionais para confrontar com o calendário regulatório.

## Escopo

1. **Tratamento** (`src/features/tratamento.py`): deflacionamento pelo IPCA,
   harmonização final de periodicidade, tratamento de ausências e outliers.
2. **Decomposição e diagnóstico** (`src/features/diagnostico.py`): decomposição
   sazonal, testes de estacionariedade (ex.: ADF, KPSS), correlação cruzada com
   defasagens entre exposição a apostas e indicadores de endividamento.
3. **Detecção de quebras estruturais** (`src/features/quebras_estruturais.py`):
   algoritmo de segmentação aplicado às séries **sem informação prévia das datas
   regulatórias** (constitution §2); confronto posterior com o calendário da proposta
   (jan/2025, out/2025, dez/2025) feito em etapa separada de validação/relato, nunca
   como input do detector.
4. **Indicador composto territorial** (`src/features/indicador_territorial.py`):
   construção do indicador de exposição por UF (Recorte 1) a partir de Google Trends +
   Portal da Transparência/CadÚnico, e caracterização descritiva dos municípios da UF
   de maior exposição (Recorte 2), usando ESTBAN. **Proibido projetar cenários** no
   Recorte 1 e **proibido modelar** no Recorte 2 (constitution §5).

## Critérios de aceite (Definition of Done)

1. `src/features/tratamento.py` tem teste unitário cobrindo: (a) deflacionamento
   correto por IPCA para uma série sintética conhecida, (b) estratégia de imputação
   documentada e testada para ao menos um caso de gap curto (≤ 2 meses) e um caso de
   gap estrutural (série que só começa em período recente — não deve ser imputada
   para trás, apenas documentada como ausente).
2. `src/features/diagnostico.py` produz, para cada série do núcleo nacional, um
   relatório (`reports/figures/eda/<serie>.png` + entrada em
   `reports/figures/eda/sumario.csv`) com: decomposição sazonal, resultado dos testes
   de estacionariedade, e correlação cruzada com defasagens de 0 a 12 meses contra o
   indicador de exposição a apostas.
3. `src/features/quebras_estruturais.py` tem teste unitário com série sintética com
   quebra conhecida em posição conhecida — o algoritmo deve recuperar a posição da
   quebra dentro de uma tolerância documentada (ex.: ±1 mês).
4. O confronto entre quebras detectadas e calendário regulatório é registrado como
   artefato explícito (`reports/figures/quebras_vs_regulacao.png` ou tabela
   equivalente), não apenas mencionado em texto — é o "teste de validade externa da
   base" citado na proposta.
5. `src/features/indicador_territorial.py` documenta a metodologia do indicador
   composto (pesos, normalização, fontes) em `docs/glossario.md` ou documento
   dedicado, e todo output territorial carrega um campo/anotação explícita
   `"exploratorio: True"` ou equivalente, propagada até o relatório final.
6. Toda transformação roda determinística (mesma entrada → mesma saída byte-a-byte
   ou numericamente idêntica dentro de tolerância declarada).

## Contrato de dados

**Entrada:** saída long-format de `specs/01-ingestao-dados` (ver contrato lá).

**Saída (`data/processed/base_nacional_corte-<data>_run-<timestamp>.parquet`):**
wide-format, uma linha por `data_referencia`, colunas = variáveis tratadas e
deflacionadas, mais colunas de flag (`<variavel>_imputado: bool`,
`<variavel>_outlier: bool`).

**Saída territorial** (`data/processed/indicador_territorial_uf.parquet`): uma linha
por UF, coluna `indicador_composto` (float, normalizado 0–1) + colunas dos
componentes usados, todas anotadas como exploratórias no dicionário de dados.

## Casos de borda

- Série com menos de 24 observações não entra em decomposição sazonal automática —
  reportar aviso explícito em vez de forçar decomposição instável.
- Outlier genuíno (ex.: pico real de Pix associado a evento noticiado) não deve ser
  removido silenciosamente — sinalizar e documentar a decisão de manter/tratar caso a
  caso, referenciando a fonte jornalística/oficial quando aplicável.
- Se o algoritmo de segmentação não detectar nenhuma quebra: isso é um resultado
  válido e deve ser reportado como tal (a proposta trata a questão como pergunta de
  pesquisa aberta — "e, em caso positivo" — não como resultado esperado).

## Fora de escopo

- Modelagem preditiva e projeção de cenários → `specs/03-modelagem`.
- Métricas de avaliação e testes estatísticos de comparação de modelos →
  `specs/04-avaliacao`.
