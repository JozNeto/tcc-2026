# ADR 0002 — Códigos de série SGS/BCB usados no núcleo nacional

- **Status:** aceito
- **Data:** 2026-08-17

## Contexto

A proposta (seção 5) exige, da fonte SGS/BCB: "endividamento das famílias,
comprometimento de renda e inadimplência da carteira de pessoas físicas". O SGS tem
milhares de séries e frequentemente descontinua/substitui séries antigas por versões
revisadas — usar o código errado silenciosamente compromete a reprodutibilidade
exigida por `specs/constitution.md` §1. Os códigos foram verificados manualmente
(consulta real à API pública + busca no Portal de Dados Abertos do BCB) em
2026-08-17, não assumidos de memória.

## Decisão

Usar os três códigos abaixo em `src/data/sgs.py` (`SERIES`):

| Variável (`nome_variavel`) | Código SGS | Nome oficial | Observação de verificação |
|---|---|---|---|
| `comprometimento_renda_pf` | **29034** | Comprometimento de renda das famílias com o serviço da dívida com o SFN — com ajuste sazonal (RNDBF) | Confirmado ativo via consulta real à API em 2026-08-17 (últimos valores: jan–mai/2026, ~28%). |
| `endividamento_familias_sfn` | **29037** | Endividamento das famílias com o SFN em relação à renda acumulada dos últimos 12 meses (RNDBF) | Confirmado via busca no Portal de Dados Abertos do BCB; valor de mar/2026 ≈ 49,8%, plausível para a métrica. |
| `inadimplencia_pf` | **21084** | Inadimplência da carteira de crédito — Pessoas físicas — Total (percentual da carteira com parcela em atraso > 90 dias) | Confirmado ativo via consulta real à API em 2026-08-17 (últimos valores: fev–jun/2026, ~5,4–5,6%). |
| `ipca_variacao_mensal` | **433** | IPCA — Índice Nacional de Preços ao Consumidor Amplo — variação mensal (%) | Confirmado ativo via consulta real à API em 2026-08-17 (últimos valores: mai–jul/2026, 0,07%–0,58%). Usado por `src/features/tratamento.py` para deflacionar as demais séries nominais do projeto (constrói-se um índice acumulado a partir da variação mensal). |

## Alternativas descartadas

- **19881 / 19882** (comprometimento de renda / endividamento, versões antigas): a
  consulta real à API mostrou que a série 19881 parou de atualizar em agosto/2021 —
  o Portal de Dados Abertos do BCB confirma que essas séries estão **"Em
  Desativação"**, substituídas por 29034/29037. Usá-las produziria uma base
  desatualizada sem qualquer erro visível no pipeline.
- **21082** ("Inadimplência da carteira de crédito — Total"): é o indicador agregado
  de **todos** os tomadores (pessoas físicas + jurídicas), não específico de pessoas
  físicas como a proposta exige. Descartado em favor de 21084, que já vem
  segmentado para pessoas físicas.
- **29038** (endividamento das famílias excluindo crédito habitacional): mantido como
  variável adicional em aberto para uma eventual análise de sensibilidade, mas não
  incluído no catálogo padrão `SERIES` — decisão de não incluir no MVP para manter o
  núcleo de variáveis enxuto; pode ser adicionado depois sem quebrar o contrato de
  dados (basta estender o dicionário `SERIES`).

## Consequências

- `src/data/sgs.py` documenta os três códigos com a fonte da verificação no
  docstring do módulo, não apenas neste ADR.
- Antes de uma nova rodada de coleta em produção (ex.: no fechamento do TCC), os
  códigos devem ser reconfirmados em https://dadosabertos.bcb.gov.br/ — séries do SGS
  podem ser descontinuadas a qualquer momento, como já ocorreu com 19881/19882.
- Se o grupo decidir incluir a série 29038 (ou outra variação) no futuro, basta
  estender `SERIES` — não requer mudança de contrato de dados, só um novo ADR se a
  decisão for não-trivial.
