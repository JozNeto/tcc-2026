# Constitution — Princípios Inegociáveis do Projeto

> Referência viva. Toda spec em `specs/` e toda skill em `.mcp/skills/` deve respeitar
> estes princípios. Em caso de conflito entre uma spec e este documento, este documento
> prevalece — abra um ADR em `docs/adr/` para propor mudança.
>
> Fonte da verdade do projeto: [`docs/00-proposta-resumo.md`](../docs/00-proposta-resumo.md),
> derivado de `proposta-tcc-apostas-online.pdf`.

## 0. Identidade do projeto

- **Tema:** Apostas online e vulnerabilidade financeira das famílias brasileiras —
  mensuração nacional, quebras estruturais e projeção de cenários (2020–2029).
- **Autoria:** trabalho em grupo (5+ integrantes).
- **Prazo:** cronograma oficial recebido — três entregas quinzenais:

  | Entrega | Início da quinzena | Vencimento | Carência (prazo final absoluto) |
  |---|---|---|---|
  | Primeira entrega | Quinzena 2 — 24/08/2026 | 01/09/2026 23:59 | 06/09/2026 23:59 |
  | Segunda entrega | Quinzena 5 — 05/10/2026 | 13/10/2026 23:59 | 18/10/2026 23:59 |
  | Entrega final | Quinzena 7 — 02/11/2026 | 10/11/2026 23:59 | 15/11/2026 23:59 |

  Ver `TASKS.md` para o escopo de cada entrega conforme for definido com o
  orientador/grupo.
- **Rubrica formal:** não há rubrica separada da UNIVESP disponível no momento. O
  critério de aderência usado é o próprio conteúdo do PDF da proposta (objetivos,
  entregáveis, etapas, delimitações), verificado via checklist em
  `docs/00-proposta-resumo.md` (seção de checklist, a preencher na Etapa 8).

## 1. Reprodutibilidade obrigatória

- Toda análise, modelo e figura reportada deve ser reprodutível a partir do código
  versionado + dados brutos (ou instruções de obtenção dos dados brutos).
- Seeds aleatórias fixas em qualquer processo estocástico (split, inicialização de
  modelo, bootstrap, simulação de cenários). A seed usada deve ser registrada junto ao
  resultado (log, metadado ou nome de arquivo).
- Pipeline parametrizado por período (data de início/fim), permitindo reconstrução e
  atualização futura por terceiros — requisito explícito da proposta (Etapa 8 /
  entregável "pipeline reprodutível").
- Ambiente declarado via `requirements.txt`/`pyproject.toml` com versões fixadas
  (pinned), não ranges abertos, para as bibliotecas centrais do pipeline analítico.

## 2. Sem vazamento de dados (data leakage)

- Por se tratar de séries temporais, é **proibido** qualquer split aleatório
  treino/teste. Validação exclusivamente por **origem móvel (rolling origin /
  walk-forward)**, conforme explicitamente exigido na Etapa 5 da proposta.
- Nenhuma transformação que dependa de estatísticas calculadas sobre o período de
  teste (ex.: normalização, imputação) pode "vazar" informação futura para o passado
  durante o treino.
- A detecção de quebras estruturais (Etapa 4) deve ser feita **sem informar
  previamente as datas regulatórias ao algoritmo** — as datas servem apenas para
  validação externa posterior do resultado, nunca como input do detector.

## 3. Data de corte fixa da base

- Data de corte adotada: **31/12/2025**. Cobre os três marcos regulatórios da
  proposta (jan/2025, out/2025, dez/2025), inclusive a decisão do STF.
- Toda extração de fonte pública deve truncar ou documentar explicitamente o motivo de
  não conseguir truncar (ex.: painel semestral cujo próximo corte natural cai fora da
  janela) na data de corte acima.
- Mudar a data de corte exige um ADR novo, não uma edição silenciosa.

## 4. Fontes de dados: preferência estrita por API oficial

- Preferir sempre acesso programático a fontes **oficiais e estáveis** (SGS/BCB,
  SIDRA/IBGE, portais com API documentada).
- **Scraping e bibliotecas não-oficiais devem ser evitados ao máximo** (decisão
  explícita do grupo). Quando uma fonte da proposta não tiver API oficial estável
  (ex.: Google Trends via `pytrends`, painéis semestrais da SPA/MF sem endpoint
  aberto, Portal da Transparência sem endpoint direto para o dado necessário):
  1. Priorizar exportações manuais oficiais (CSV/XLSX disponibilizado no próprio
     portal) sobre scraping de HTML.
  2. Se não houver alternativa sem scraping, declarar a limitação explicitamente no
     dicionário de dados e na monografia — não substituir silenciosamente a fonte.
  3. Avaliar reduzir o escopo do indicador afetado (especialmente os indicadores
     territoriais dos Recortes 1 e 2, que a própria proposta já trata como
     exploratórios) em vez de depender de scraping frágil.
- Nenhuma coleta de dados pessoais ou não públicos. Todas as fontes devem ser
  agregadas e de acesso público, conforme delimitação da proposta (seção 8:
  "inferência agregada").

## 5. Escopo fiel à proposta

- **Núcleo (Brasil, série nacional mensal):** EDA completa, detecção de quebras,
  modelagem preditiva comparativa, projeção de cenários. É o único nível com
  modelagem preditiva e projeção.
- **Recorte 1 (27 UFs):** indicador composto de exposição + ordenamento comparativo.
  **Proibido projetar cenários neste nível** — a proposta é explícita: "sem projeção".
- **Recorte 2 (municípios da UF identificada):** caracterização descritiva apenas.
  **Proibido modelar neste nível** — a proposta é explícita: "sem modelagem".
- O trabalho **não** formula política pública, **não** avalia eficácia regulatória e
  **não** estabelece causalidade em nível individual. Qualquer código ou texto que
  produza esse tipo de conclusão está fora do escopo aprovado.
- O indicador territorial (Recortes 1 e 2) deve sempre ser apresentado com a
  qualificação explícita de "aproximação por fontes indiretas, não medição oficial".

## 6. Validação estatística rigorosa

- Comparação de modelos de previsão sempre inclui: (a) baseline ingênuo obrigatório
  (ex.: naive, seasonal naive), (b) validação por origem móvel, (c) métrica de erro
  relativo, (d) teste estatístico de diferença de desempenho — os quatro elementos são
  exigência textual da proposta (Etapa 5), nenhum é opcional.
- Toda projeção de cenário deve reportar intervalo de predição explícito, nunca apenas
  a estimativa pontual (exigência textual da Etapa 6).
- O cenário inercial deve ser rotulado como condicional à estabilidade regulatória —
  nunca apresentado como previsão incondicional, dado que a própria cronologia recente
  contraria essa premissa (risco já declarado na proposta, seção 8).
- Horizonte de projeção principal: 24 meses. Qualquer horizonte além disso deve ser
  rotulado como "exercício de cenário", nunca como "previsão".

## 7. Publicação e dados abertos (FAIR)

- Base de dados final publicada com licença aberta e identificador persistente (ex.:
  Zenodo DOI) — entregável obrigatório da proposta.
- Código publicado em repositório versionado, com dicionário de dados e nota
  metodológica.
- Painel interativo de consulta aos resultados: **Streamlit** (decisão do grupo),
  integrado ao pipeline Python existente para minimizar duplicação de lógica entre
  análise e visualização.

## 8. Qualidade acadêmica

- Citações conforme **ABNT NBR 6023** (única norma explicitamente citada na proposta).
- Estrutura geral da monografia segue **ABNT NBR 14724** como padrão de fallback, na
  ausência de template institucional específico — revisar se a UNIVESP fornecer um
  template próprio futuramente (ver `docs/00-proposta-resumo.md`, ponto 7 da seção 12).
- Toda fonte de dado, biblioteca com metodologia relevante (ex.: algoritmo de detecção
  de quebras estruturais) ou referência teórica usada deve ser rastreada em
  `docs/referencias.md` desde o início — não apenas no fechamento do trabalho.

## 9. Definition of Done (aplica-se a toda spec em `specs/`)

Uma spec só é considerada implementada quando:
1. O código correspondente existe em `src/` (ou `tests/`, `.mcp/`, conforme o caso).
2. Os critérios de aceite da spec estão cobertos por teste automatizado em `tests/`.
3. `make test` (ou equivalente) passa, incluindo o harness de qualidade de dados
   quando a spec envolve dados.
4. A skill MCP relevante (se houver) foi consultada/atualizada.
5. `TASKS.md` e `CHANGELOG.md` foram atualizados.
