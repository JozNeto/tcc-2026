# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Entradas datadas por marco/entrega relevante, não por commit individual.

## [Não lançado]

### Adicionado — 2026-09-20
- **Projeção univariada do crédito** (`pipeline/scripts/projetar_credito.py`): SARIMAX de 24 meses com
  validação por origem móvel, MASE, Diebold-Mariano e cobertura de intervalo; incluída na V1 (Seção 4.7,
  Tabelas 6–7, Figura 3). Nenhum modelo supera o naive de forma significativa.
- **V1 da entrega final** (`reports/final/TCC_V1_entrega_final.docx`, gerada por
  `reports/final/gerar_v1_entrega_final.py`) a partir do `.docx` da Primeira Entrega editado
  pelo grupo (preserva capa com RAs, folha de aprovação, sumário automático e referências).
  Inclui Metodologia detalhada (Python 3.12.3, bibliotecas com versões, métodos estatísticos,
  auditoria), Resultados e Discussão, Conclusão, novas referências e Apêndices A (cronograma)
  e B (reprodução). Todos os números são calculados dos dados do pipeline.
- Pipeline isolado (`pipeline/`): coleta real (SGS, IBGE, Bolsa Família em fatias, Google
  Trends), análise da pergunta central, 175 testes, CI. `requirements.txt` agora fixa as
  versões efetivamente usadas nos resultados (antes divergiam); CI em Python 3.12.
- ADR 0004 (definições das fontes manuais) e ADR 0005 (Google Trends via pytrends, exceção
  ao ADR 0001).

### Adicionado — 2026-09-03
- `docs/cronograma_equipe.md` — cronograma técnico do grupo (Quinzenas 3–7),
  atribuindo cada um dos 8 integrantes a uma frente de trabalho específica do
  pipeline (coleta API, coleta manual, tratamento/EDA, quebras estruturais/
  indicador territorial, modelagem, cenários/avaliação, relatório/dashboard/
  literatura, gestão/integração/redação final).
- `TASKS.md` atualizado: campo "Dono do módulo" de cada seção preenchido conforme
  o cronograma da equipe (era "a definir").
- `reports/final/cronograma_tcc.docx` (gerado por `reports/final/gerar_cronograma.py`)
  — versão do cronograma em registro acadêmico, sem menção a arquivos de código-fonte,
  destinada à inserção na monografia/avaliação. Complementa, sem substituir,
  `docs/cronograma_equipe.md` (documento de gestão interna do projeto, que continua
  sendo a fonte da verdade técnica sobre "quem faz o quê").

### Adicionado — 2026-09-01
- Cronograma oficial de TCC recebido e incorporado a `specs/constitution.md` §0 e
  `TASKS.md`: Primeira Entrega (venc. 01/09/2026, carência 06/09/2026), Segunda
  Entrega (venc. 13/10/2026, carência 18/10/2026), Entrega Final (venc. 10/11/2026,
  carência 15/11/2026).
- **Relatório parcial da Primeira Entrega produzido e entregue ao grupo**
  (`reports/parcial/relatorio_parcial_primeira_entrega.docx`, gerado por
  `reports/parcial/gerar_relatorio_parcial.py`), seguindo a estrutura do template
  institucional (`modelos_anteriores_tcc/Modelo_Projeto_TCC_Científico.docx`) e as
  convenções de formatação dos TCCs anteriores do curso de Ciência de Dados
  (capa, folha de rosto, resumo, sumário, fundamentação teórica preliminar,
  metodologia, cronograma, referências).
- Levantamento preliminar de literatura acadêmica real (não inventada) sobre
  apostas online e vulnerabilidade financeira, com fontes verificadas por busca:
  Baker et al. (2024, NBER Working Paper 33108); Santos, Coelho e Bernardes (2025,
  Revista Ibero-Americana de Humanidades, Ciências e Educação); CNC/Geade (2026).
- Nota de correção: documentos anteriores desta sessão (ADRs, CHANGELOG,
  docstrings de `src/data/`) foram datados incorretamente como 2026-08-17 — a data
  real da sessão é 2026-09-01. Não foram corrigidos retroativamente (baixo valor,
  alto custo de edição em massa); entradas futuras usam a data correta.

### Adicionado — 2026-08-17 (nota: ver correção de data acima)
- Estrutura inicial do projeto (`docs/`, `specs/`, `.mcp/`, `src/`, `tests/`,
  `notebooks/`, `data/`, `reports/`).
- `docs/00-proposta-resumo.md` — resumo estruturado da proposta de TCC.
- `specs/constitution.md` — princípios inegociáveis do projeto (reprodutibilidade,
  ausência de vazamento de dados, escopo por camada, data de corte 31/12/2025,
  preferência estrita por fontes com API oficial).
- Specs dos 5 módulos (`specs/01-ingestao-dados` a `specs/05-relatorio-entrega`).
- `docs/adr/0001-registro-inicial.md` — primeiro ADR, registrando decisões
  fundacionais (data de corte, ferramenta de dashboard, política de scraping).
- `CONTRIBUTING.md` — convenções de commit (Conventional Commits) e branches para
  grupo de 5+ integrantes.
- Decisões fundacionais confirmadas com o grupo: data de corte 31/12/2025; trabalho
  em grupo (5+ pessoas); painel interativo em Streamlit; scraping evitado ao máximo
  (preferência estrita por fontes com API oficial); sem rubrica formal disponível —
  usar ABNT NBR 14724 como fallback estrutural.
- `docs/tdd.md` — Technical Design Document, com diagrama de arquitetura, stack
  tecnológica, fluxo de dados ponta a ponta e mapeamento de cada requisito da
  proposta para o componente que o implementa.
- Servidor MCP local (`.mcp/server.py`, `.mcp/config.json`, `.mcp.json` na raiz) e as
  6 skills do projeto (`contexto-proposta`, `validacao-dados`, `eda`, `modelagem`,
  `avaliacao-metrica`, `redacao-academica`), com gate que recusa consultar skills de
  modelagem/avaliação/redação antes de `consultar_contexto_proposta`.
- Harness de testes inicial: validadores reutilizáveis de qualidade de dados
  (`tests/data_quality/validadores.py`) e harness de regressão de métricas de modelo
  (`tests/model_eval_harness/harness.py` + `limiares.py`), ambos com cobertura de
  testes unitários.
- `requirements.txt`, `pytest.ini`, `Makefile` (alvos `setup`, `test`, `test-network`,
  `lint`, `dashboard`, `mcp`, `clean`).
- `docs/glossario.md` e `docs/referencias.md` — rastreamento inicial de termos e
  fontes citadas na proposta, a expandir conforme cada módulo for implementado.
- Primeiro módulo real de ingestão: `src/data/sgs.py` (spec 01), coletando as três
  séries do núcleo nacional exigidas pela proposta via API pública do SGS/BCB —
  comprometimento de renda (série 29034), endividamento das famílias (série 29037) e
  inadimplência de pessoas físicas (série 21084). Códigos verificados contra a API
  real e o Portal de Dados Abertos do BCB (não assumidos de memória) — ver
  `docs/adr/0002-series-sgs-nucleo-nacional.md`, que também documenta por que as
  séries antigas 19881/19882 foram descartadas (descontinuadas pelo BCB em 2021).
- Testes unitários com fixtures gravadas (`tests/unit/test_sgs.py`, sem rede) e teste
  de integração real marcado `@pytest.mark.network`
  (`tests/integration/test_sgs_integration.py`), validado contra a API ao vivo do BCB
  nesta sessão.
- Suíte de testes local: 31 testes unitários/data-quality/harness passando via
  `make test`, mais 1 teste de integração de rede passando via `make test-network`.

### Adicionado — 2026-08-17 (pipeline completo, specs 01–05)

**Ingestão (`src/data/`, spec 01) — todas as 8 fontes da proposta:**
- `ibge.py` — API SIDRA real (taxa de desocupação tabela 6381, PMC tabela 8880,
  população tabela 6579, todos os códigos verificados ao vivo).
- `transparencia.py` — API real do Portal da Transparência (Novo Bolsa Família por
  município), token via `PORTAL_TRANSPARENCIA_TOKEN` (`.env.example` criado).
- `google_trends.py` — parser dos dois formatos nativos de CSV exportado pelo Google
  Trends (regional e temporal) — decisão explícita de **não** usar `pytrends`.
- `peic.py`, `epae.py`, `spa_mf.py`, `estban.py` — sem API oficial estável confirmada
  (verificado, não assumido) — leem exportação manual normalizada de `data/raw/`,
  documentado em `docs/adr/0003-estrategia-de-acesso-por-fonte.md`.
- `_comum.py` — utilitários compartilhados entre os 8 módulos de coleta.
- Série de IPCA (429 → **433**, variação mensal) adicionada a `sgs.py` para uso do
  deflacionamento.
- `docs/adr/0003-estrategia-de-acesso-por-fonte.md` — mapeia, fonte a fonte, qual
  tem API confirmada vs. qual usa exportação manual, e por quê.

**Tratamento, EDA e territorial (`src/features/`, spec 02):**
- `tratamento.py` — índice deflator construído a partir do IPCA (ancorado numa data
  base), imputação de gaps curtos interiores (runs ≤ N observações, gaps estruturais
  nas bordas nunca imputados), sinalização de outliers por desvio-padrão.
- `diagnostico.py` — ADF + KPSS (`avaliar_estacionariedade`), decomposição sazonal
  com guarda para séries < 24 observações, correlação cruzada com defasagens 0–12.
- `quebras_estruturais.py` — detecção via `ruptures` (Pelt automático por penalidade
  ou Binseg com nº de quebras fixo), nunca informando datas regulatórias ao
  detector; `confrontar_com_calendario_regulatorio()` faz o cruzamento depois, como
  etapa de validação externa separada.
- `indicador_territorial.py` — indicador composto normalizado min-max com pesos
  configuráveis (Recorte 1) e caracterização puramente descritiva de municípios
  (Recorte 2) — nenhuma das duas funções aceita horizonte de projeção ou ajusta
  modelo (specs/constitution.md §5 impossível de violar via a API oferecida).

**Modelagem (`src/models/`, spec 03):**
- `base.py` — interface comum `ModeloSerie` (fit/predict) + `validar_saida_previsao`.
- `baseline.py` — `NaiveModel` e `SeasonalNaiveModel`, com intervalo de predição.
- `econometricos.py` — `SARIMAXModel` (com/sem variável exógena).
- `ml_series.py` — `MLSeriesModel`, gradient boosting sobre features de defasagem,
  previsão recursiva multi-passo, sem vazamento.
- `validacao.py` — `validar_rolling_origin`, único método de validação usado no
  projeto (specs/constitution.md §2).
- `cenarios.py` — `projetar_cenarios` (inercial/contenção/expansão), rótulo
  `condicional_a_regulacao_estavel` no inercial e `tipo="exercicio_de_cenario"` para
  passos além de `HORIZONTE_PRINCIPAL_MESES=24`.
- `custo_patrimonial.py` — simulação Monte Carlo com seed fixa, validada contra a
  fórmula fechada de anuidade (`aporte * (1+r) * ((1+r)^T - 1)/r`).

**Avaliação (`src/evaluation/`, spec 04):**
- `metricas.py` — MASE, sMAPE, RMSE, MAE, valores conferidos à mão em teste.
- `testes_estatisticos.py` — `calcular_diebold_mariano` com correção de pequena
  amostra (Harvey-Leybourne-Newbold) e `corrigir_bonferroni` para múltiplas
  comparações.
- `validacao_territorial.py` — correlação com proxy conhecido e estabilidade do
  ranking de UFs a perturbação de pesos (Spearman) — documentado como checagem de
  plausibilidade, nunca como validação estatística de acurácia.

**Relatório e publicação (`src/reporting/`, `src/dashboard/`, spec 05):**
- `reporting/figuras.py` — plot de série+intervalo de predição e de cenários
  comparativos (matplotlib, backend `Agg`).
- `reporting/manifesto.py` — proveniência rastreável por figura publicada.
- `dashboard/app.py` — painel Streamlit somente leitura/visualização de
  `data/processed/`, sem nenhuma lógica de cálculo.
- `tests/integration/test_dashboard_smoke.py` — smoke test via
  `streamlit.testing.v1.AppTest`, roda em `make test` (não precisa de rede).
- `Makefile` corrigido: `make test` agora inclui `tests/integration` filtrando
  `-m "not network"` — antes, testes de integração sem marca `network` (como o smoke
  test do dashboard) não rodavam em lugar nenhum.

**Qualidade e correções encontradas durante a validação:**
- Renomeadas `testar_estacionariedade` → `avaliar_estacionariedade` e
  `teste_diebold_mariano` → `calcular_diebold_mariano` (e a exceção
  `TesteEstatisticoError` → `EstatisticaError`): nomes começando com `test`/`teste`
  colidiam com a descoberta de testes do pytest quando importados em um módulo de
  teste — ver nota nova em `CONTRIBUTING.md`.
- Suíte completa validada nesta sessão: **161 testes passando** (159 sem rede via
  `make test` + 2 de integração real via `make test-network`, contra as APIs reais
  do BCB/SGS e IBGE/SIDRA).

### Pendente para a próxima sessão de trabalho
- Repositório ainda não é um `git init` — nenhum commit foi feito (decisão do
  usuário: só versionar depois de testar localmente).
- Prazo de entrega/defesa e donos de módulo por integrante do grupo ainda não
  definidos (ver `TASKS.md`).
- Nenhum módulo rodou ainda contra dados reais coletados de ponta a ponta — toda a
  suíte de testes usa dados sintéticos ou fixtures gravadas; falta orquestrar
  `src/data/` → `src/features/` → `src/models/` → `src/evaluation/` →
  `src/reporting/`/`src/dashboard/` num pipeline real (`make run-pipeline` ou
  similar, ainda não existe).
- Arquivos reais de exportação manual (PEIC, EPAE, SPA/MF, Google Trends, ESTBAN)
  ainda não foram coletados/colocados em `data/raw/`.
- ADR pendente: escolha entre MASE e sMAPE como métrica de decisão principal.
- `docs/dicionario_dados.md`, `docs/nota_metodologica.md`, checklist de aderência à
  proposta e a monografia em si ainda não foram escritos.
