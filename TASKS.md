# TASKS

Plano de execução derivado das specs em `specs/`. Status: `todo` / `doing` / `done`.
Dono de módulo: preencher com o nome do integrante responsável assim que o grupo se
dividir — até lá, "a definir".

## Etapa 0 — Proposta e fundação do projeto

| Tarefa | Status | Dono |
|---|---|---|
| Ler proposta e produzir `docs/00-proposta-resumo.md` | done | — |
| Resolver ambiguidades da proposta com o grupo (data de corte, autoria, painel, rubrica) | done | — |
| Criar estrutura de diretórios (`docs/`, `specs/`, `.mcp/`, `src/`, `tests/`, `data/`, `reports/`) | done | — |
| Escrever `specs/constitution.md` | done | — |
| Escrever specs dos 5 módulos | done | — |
| `CONTRIBUTING.md`, `.gitignore`, `README.md` | done | — |
| Configurar servidor MCP local + skills (`.mcp/`) | done | — |
| Escrever `docs/tdd.md` | done | — |
| Harness de testes base (`tests/`) — validadores de qualidade de dados + harness de regressão de métricas, 23 testes passando | done | — |
| `docs/adr/0001-registro-inicial.md` | done | — |
| `docs/glossario.md`, `docs/referencias.md` | done | — |
| `requirements.txt`, `pytest.ini`, `Makefile` | done | — |
| Inicializar repositório git (projeto ainda não é um repo) | todo | — |
| `make setup` real (instalar `requirements.txt` completo, não só pandas/pytest usados na validação do harness) | todo | — |

## Módulo `src/data/` — Ingestão (spec: `specs/01-ingestao-dados/spec.md`)

Dono do módulo: Fabiano Guilherme Dionizio Bortolussi (fontes com API oficial —
sgs.py, ibge.py, transparencia.py) e José Araújo Neto (fontes manuais — peic.py,
epae.py, spa_mf.py, google_trends.py, estban.py). Ver `docs/cronograma_equipe.md`.

| Tarefa | Status | Dono |
|---|---|---|
| `src/data/sgs.py` — coleta SGS/BCB (endividamento, comprometimento de renda, inadimplência PF) — séries 29034/29037/21084 verificadas, ver `docs/adr/0002-series-sgs-nucleo-nacional.md` | done | — |
| `src/data/peic.py` — PEIC/CNC. Sem API/export oficial confirmada — lê exportação manual normalizada em `data/raw/peic/` (ver ADR 0003) | done (aguarda arquivo real de `data/raw/`) | — |
| `src/data/epae.py` — EPAE/BCB. Estatística nova, sem dataset aberto confirmado — exportação manual (ADR 0003) | done (aguarda arquivo real) | — |
| `src/data/spa_mf.py` — painéis semestrais SPA/MF. Sem API pública — exportação manual long-format (ADR 0003) | done (aguarda arquivo real) | — |
| `src/data/google_trends.py` — parser do CSV nativo exportado do Google Trends (regional + temporal), sem `pytrends`/scraping | done (aguarda arquivo real) | — |
| `src/data/transparencia.py` — Portal da Transparência (Novo Bolsa Família por município), API real com token — ver `.env.example` | done | — |
| `src/data/estban.py` — ESTBAN/BCB (Recorte 2). URL de download não confirmada com segurança — exportação manual (ADR 0003) | done (aguarda arquivo real) | — |
| `src/data/ibge.py` — IBGE/SIDRA (taxa de desocupação, PMC, população) — API real verificada | done | — |
| `src/data/_comum.py` — utilitários compartilhados (contrato long-format, truncamento por data de corte, leitor de exportação manual) | done | — |
| Testes unitários (fixtures, sem rede) para cada módulo acima | done (sgs, ibge, transparencia, comum, peic, epae, spa_mf, estban, google_trends) | — |
| Testes de integração (`@pytest.mark.network`) — feito para sgs e ibge; transparencia precisa de token real para testar ao vivo | parcial | — |
| `.env.example` (token do Portal da Transparência) | done | — |
| Obter os arquivos reais de exportação manual (PEIC, EPAE, SPA/MF, Google Trends, ESTBAN) e colocá-los em `data/raw/` | todo | — |

## Módulo `src/features/` — Limpeza, EDA, Quebras (spec: `specs/02-limpeza-eda/spec.md`)

Dono do módulo: Josué Dantas Martins (tratamento.py, diagnostico.py) e Palmira da
Conceição João (quebras_estruturais.py, indicador_territorial.py). Ver
`docs/cronograma_equipe.md`.

| Tarefa | Status | Dono |
|---|---|---|
| `src/features/tratamento.py` — deflacionamento IPCA (índice construído a partir da série 433), imputação de gaps curtos (interior, ≤2 obs por padrão), sinalização de outliers | done | — |
| `src/features/diagnostico.py` — ADF + KPSS, decomposição sazonal (com guarda para série < 24 obs), correlação cruzada com defasagens 0–12 | done | — |
| `src/features/quebras_estruturais.py` — detecção via `ruptures` (Pelt automático ou Binseg com nº de quebras fixo), sem informar datas regulatórias ao detector | done | — |
| Confronto quebras detectadas × calendário regulatório (artefato explícito) | done — `confrontar_com_calendario_regulatorio()` | — |
| `src/features/indicador_territorial.py` — indicador composto por UF (Recorte 1), normalização min-max, pesos configuráveis | done | — |
| Caracterização descritiva dos municípios da UF identificada (Recorte 2) | done — `caracterizar_municipios()`, puramente descritivo | — |
| Documentar metodologia do indicador composto em `docs/glossario.md` | parcial — termos documentados; metodologia completa (pesos escolhidos, fontes finais) fica para quando os dados reais entrarem | — |
| Rodar o pipeline `tratamento → diagnostico → quebras_estruturais → indicador_territorial` sobre dados reais coletados (ainda não rodou fim-a-fim, só testado com dados sintéticos) | todo | — |

## Módulo `src/models/` — Modelagem e Cenários (spec: `specs/03-modelagem/spec.md`)

Dono do módulo: Pedrina Ferreira Gomes (baseline.py, econometricos.py, ml_series.py,
validacao.py) e Vinícius Figueiredo Dias Nunes (cenarios.py, custo_patrimonial.py).
Ver `docs/cronograma_equipe.md`.

| Tarefa | Status | Dono |
|---|---|---|
| `src/models/base.py` — interface comum `ModeloSerie` (fit/predict) + validador de contrato de saída | done | — |
| `src/models/baseline.py` — naive / seasonal naive, com intervalo de predição | done | — |
| `src/models/econometricos.py` — SARIMAX (com/sem exógena) | done | — |
| `src/models/ml_series.py` — gradient boosting (scikit-learn) sobre features de defasagem, sem vazamento, previsão recursiva multi-passo | done | — |
| `src/models/validacao.py` — rolling origin / walk-forward, único método de validação usado | done | — |
| ADR escolhendo métrica de erro relativo (MASE vs. sMAPE) | todo — ambas implementadas em `src/evaluation/metricas.py`, falta decidir qual é a métrica de decisão principal | — |
| `src/models/cenarios.py` — projeção N meses, 3 cenários (inercial/contenção/expansão), intervalos de predição, rótulo `condicional_a_regulacao_estavel` e `tipo` (previsao vs. exercício de cenário além de 24 meses) | done | — |
| `src/models/custo_patrimonial.py` — simulação Monte Carlo com seed fixa, validada contra fórmula fechada de anuidade | done | — |
| Calibrar `order`/`seasonal_order` do SARIMAX e hiperparâmetros do ML sobre as séries reais (hoje só testado com dados sintéticos) | todo | — |

## Módulo `src/evaluation/` — Avaliação (spec: `specs/04-avaliacao/spec.md`)

Dono do módulo: Vinícius Figueiredo Dias Nunes. Ver `docs/cronograma_equipe.md`.

| Tarefa | Status | Dono |
|---|---|---|
| `src/evaluation/metricas.py` — MASE, sMAPE, RMSE, MAE | done | — |
| `src/evaluation/testes_estatisticos.py` — Diebold-Mariano com correção de pequena amostra (Harvey-Leybourne-Newbold) + correção de Bonferroni para múltiplas comparações | done | — |
| `tests/model_eval_harness/` — harness de regressão entre execuções | done (Etapa 0) | — |
| `src/evaluation/validacao_territorial.py` — correlação com proxy + estabilidade do ranking a perturbação de pesos (Spearman) | done | — |

## Módulo `src/reporting/` + `src/dashboard/` — Relatório e Publicação (spec: `specs/05-relatorio-entrega/spec.md`)

Dono do módulo: Wilton da Silva Alves (reporting/, dashboard/, revisão de literatura)
e Yan Ferreira Martins (referências ABNT, checklist de aderência, consolidação da
monografia e publicação da base). Ver `docs/cronograma_equipe.md`.

| Tarefa | Status | Dono |
|---|---|---|
| `src/reporting/figuras.py` — plot de série+intervalo e de cenários comparativos | done | — |
| `src/reporting/manifesto.py` — proveniência rastreável por figura (`reports/final/figuras/manifesto.csv`) | done | — |
| `src/dashboard/app.py` — painel Streamlit (só leitura de `data/processed/`, sem cálculo) | done | — |
| `tests/integration/test_dashboard_smoke.py` — teste de fumaça via `streamlit.testing.v1.AppTest`, roda em `make test` | done | — |
| `docs/dicionario_dados.md` | todo — só faz sentido depois que a base real for gerada | — |
| `docs/nota_metodologica.md` | todo | — |
| Consolidar `docs/referencias.md` em ABNT NBR 6023 | todo — hoje tem entradas provisórias, faltam autor institucional completo e data de acesso | — |
| Checklist de aderência à proposta (cruzar entregáveis vs. artefatos produzidos) | todo | — |
| Publicar base final com identificador persistente (Zenodo ou similar) | todo | — |
| Redigir monografia (`reports/final/`) | todo | — |

## Fundamentação teórica (Etapa 1 da proposta)

| Tarefa | Status | Dono |
|---|---|---|
| Revisão da literatura sobre jogos de azar e finanças domiciliares | parcial — levantamento preliminar feito para o relatório da Primeira Entrega (Baker et al. 2024; Santos, Coelho e Bernardes 2025; CNC/Geade 2026), aprofundar até a Segunda Entrega | — |
| Sistematização do calendário normativo brasileiro (já resumido em `docs/00-proposta-resumo.md` §4, expandir para a monografia) | parcial — incorporado ao relatório da Primeira Entrega | — |

## Cronograma oficial (recebido do grupo)

| Entrega | Vencimento | Carência | Escopo definido? |
|---|---|---|---|
| Primeira entrega | 01/09/2026 23:59 | 06/09/2026 23:59 | done — `reports/parcial/relatorio_parcial_primeira_entrega.docx` |
| Segunda entrega | 13/10/2026 23:59 | 18/10/2026 23:59 | a definir |
| Entrega final | 10/11/2026 23:59 | 15/11/2026 23:59 | a definir |

Ver `specs/constitution.md` §0 para a tabela completa com início de quinzena.

## Primeira Entrega — relatório parcial

- `reports/parcial/gerar_relatorio_parcial.py` — script reprodutível que gera o
  `.docx` a partir do conteúdo do projeto (specs, TDD, ADRs, estado da implementação).
- `reports/parcial/relatorio_parcial_primeira_entrega.docx` — entregável, seguindo a
  estrutura do template institucional (`modelos_anteriores_tcc/Modelo_Projeto_TCC_Científico.docx`)
  e as convenções de formatação dos TCCs anteriores do curso: capa, folha de rosto,
  resumo, sumário, introdução, fundamentação teórica preliminar, metodologia (com
  seção de estado atual da implementação), cronograma, referências.
- **Revisar antes de submeter:** conferir nomes/acentuação dos 8 autores, confirmar
  se a "Avaliador Externo" deve aparecer na folha de rosto neste estágio (o template
  oficial de "Projeto" não tem folha de aprovação com banca — incluímos a informação
  de forma simples, sem uma cerimônia formal de aprovação), e verificar se o
  orientador exige algum ajuste de formatação específico não coberto pelo template.

## Pendências que dependem de informação externa

- Escopo exato de cada entrega (o que precisa estar pronto na Primeira entrega vs.
  Segunda vs. Final) ainda não definido — depende de orientação da UNIVESP/orientador.
- Divisão de donos por módulo definida em `docs/cronograma_equipe.md` (proposta
  inicial) — confirmar com o grupo se cada um concorda com sua frente de trabalho.
