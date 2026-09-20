# Cronograma da Equipe

Cronograma técnico do grupo, derivado do plano de execução em [`TASKS.md`](../TASKS.md)
e alinhado ao **cronograma oficial de quinzenas da UNIVESP** (ver
[`specs/constitution.md`](../specs/constitution.md) §0). As Quinzenas 0–2 já foram
cumpridas (especificação do projeto, arquitetura, implementação inicial e a Primeira
Entrega); este documento detalha as Quinzenas 3–7 com responsável por atividade.

> Esta é uma proposta inicial de divisão — qualquer integrante pode propor troca de
> frente de trabalho. O importante é que cada frente tenha sempre um dono claro, para
> evitar que uma tarefa fique sem responsável (ver `CONTRIBUTING.md`).

## Frentes de trabalho (uma por integrante)

| # | Integrante | Frente de trabalho | Módulos/artefatos sob responsabilidade |
|---|---|---|---|
| 1 | Fabiano Guilherme Dionizio Bortolussi | Coleta — fontes com API oficial | `src/data/sgs.py`, `ibge.py`, `transparencia.py`; execução real da coleta, `.env` com token |
| 2 | José Araújo Neto | Coleta — fontes manuais | `src/data/peic.py`, `epae.py`, `spa_mf.py`, `google_trends.py`, `estban.py`; obtenção e normalização dos arquivos em `data/raw/` |
| 3 | Josué Dantas Martins | Tratamento e EDA | `src/features/tratamento.py`, `diagnostico.py`; execução sobre a base real e documentação dos achados |
| 4 | Palmira da Conceição João | Quebras estruturais e indicador territorial | `src/features/quebras_estruturais.py`, `indicador_territorial.py`; confronto com o calendário regulatório |
| 5 | Pedrina Ferreira Gomes | Modelagem preditiva | `src/models/baseline.py`, `econometricos.py`, `ml_series.py`, `validacao.py`; calibração sobre dados reais; ADR MASE vs. sMAPE |
| 6 | Vinícius Figueiredo Dias Nunes | Cenários e avaliação de modelos | `src/models/cenarios.py`, `custo_patrimonial.py`, `src/evaluation/`; comparação de modelos (Diebold-Mariano) |
| 7 | Wilton da Silva Alves | Relatório, dashboard e literatura | `src/reporting/`, `src/dashboard/app.py`; aprofundamento da fundamentação teórica; `docs/dicionario_dados.md`, `docs/nota_metodologica.md` |
| 8 | Yan Ferreira Martins | Gestão, integração e redação final | `TASKS.md`/`specs/`/ADRs; `docs/referencias.md` (ABNT); checklist de aderência; consolidação da monografia; publicação da base |

## Quinzena a quinzena

### Quinzena 0–2 (27/07 – 06/09/2026) — concluído
Especificação do projeto (specs, constitution, TDD, ADRs), MCP local, harness de
testes, 27 módulos de `src/` implementados e testados com dados sintéticos/fixtures
(161 testes), 3 fontes já integradas a API real. **Primeira Entrega enviada**
(`reports/parcial/relatorio_parcial_primeira_entrega.docx`).

### Quinzena 3 (07/09 – 20/09/2026)
| Integrante | Atividade |
|---|---|
| Fabiano | Solicitar/validar token do Portal da Transparência; rodar coleta real de SGS, IBGE e Portal da Transparência; conferir contra `data_corte` (31/12/2025) |
| José | Obter os 5 arquivos de exportação manual (PEIC, EPAE, SPA/MF, Google Trends, ESTBAN) e normalizá-los conforme o formato exigido em cada módulo de `src/data/` |
| Josué | Preparar ambiente para rodar `tratamento.py`/`diagnostico.py` assim que a base consolidada estiver disponível |
| Demais | Acompanhar `make test` continua passando a cada nova fonte integrada |

### Quinzena 4 (21/09 – 04/10/2026)
| Integrante | Atividade |
|---|---|
| Josué | Rodar tratamento (deflacionamento, imputação, outliers) e diagnóstico (estacionariedade, sazonalidade, correlação cruzada) sobre a base real; documentar resultados |
| Palmira | Rodar detecção de quebras estruturais sobre as séries tratadas; confrontar com o calendário regulatório; iniciar indicador composto territorial |
| Pedrina | Iniciar calibração dos modelos (baseline já não precisa de calibração; ajustar `order`/`seasonal_order` do SARIMAX e hiperparâmetros do ML) |
| Wilton | Aprofundar a revisão de literatura (Etapa 1 da proposta) |

### Quinzena 5 (05/10 – 17/10/2026) — **Segunda Entrega** (venc. 13/10, carência 18/10)
| Integrante | Atividade |
|---|---|
| Pedrina | Concluir comparação de modelos sob rolling origin; registrar ADR MASE vs. sMAPE |
| Vinícius | Rodar métricas de erro e teste de Diebold-Mariano; consolidar tabela comparativa de modelos |
| Palmira | Concluir indicador territorial (Recorte 1) e caracterização de municípios (Recorte 2) |
| Yan + Wilton | Redigir e consolidar o relatório da Segunda Entrega (resultados preliminares de quebras estruturais e comparação de modelos) |

### Quinzena 6 (18/10 – 01/11/2026)
| Integrante | Atividade |
|---|---|
| Vinícius | Rodar projeção de cenários (inercial/contenção/expansão) e simulação de custo patrimonial sobre o modelo campeão |
| Wilton | Popular o dashboard com a base real; gerar figuras finais com proveniência registrada (`manifesto.csv`) |
| Yan | Checklist de aderência à proposta; consolidar `docs/referencias.md` em ABNT NBR 6023; `docs/dicionario_dados.md`, `docs/nota_metodologica.md` |
| Fabiano + José | Apoio geral, resolução de pendências de dados que ainda faltarem |

### Quinzena 7 (02/11 – 14/11/2026) — **Entrega Final** (venc. 10/11, carência 15/11)
| Integrante | Atividade |
|---|---|
| Todos | Revisão cruzada da monografia completa (`reports/final/`) |
| Yan | Consolidação final da monografia; publicação da base com identificador persistente (Zenodo ou similar) |
| Wilton | Vídeo de apresentação do TCC; ajustes finais do dashboard |
| Pedrina + Vinícius | Ajustes finais de modelagem/cenários, se necessário, a partir da revisão do orientador |

## Observações

- As datas de vencimento/carência das entregas são as oficiais da UNIVESP (ver
  `specs/constitution.md` §0) — não são negociáveis pelo grupo.
- A divisão por pessoa é por **frente de trabalho principal**, não exclusividade: como
  o pipeline é sequencial (coleta → tratamento → modelagem → avaliação → relatório),
  espera-se colaboração entre frentes vizinhas a cada quinzena.
- Atualize este arquivo (e `TASKS.md`) sempre que a divisão mudar, para manter uma
  única fonte da verdade sobre quem é responsável por quê.
