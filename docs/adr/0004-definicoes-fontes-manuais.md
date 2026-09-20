# ADR 0004 — Definições metodológicas das fontes de coleta manual

- **Status:** aceito
- **Data:** 2026-09-20

## Contexto
Google Trends, EPAE, PEIC, SPA/MF e ESTBAN dependem de download manual. Sem definições
fixas, cada integrante escolheria termo, período e série de um jeito, comprometendo a
reprodutibilidade (constitution §1).

## Decisão
Especificação em `pipeline/docs/COLETA_MANUAL.md`:
- **Período comum:** 01/01/2020–31/12/2025 (EPAE desde nov/2020).
- **Google Trends:** termos de pesquisa `apostas online` (principal), `bet` e
  `jogo do tigrinho` (sensibilidade), Brasil, todas as categorias, pesquisa na web; um
  arquivo temporal com os 3 termos e um regional por termo.
- **EPAE:** fluxo Pix Famílias → CNAE seção R (artes, cultura, esporte e recreação).
- **PEIC:** total Brasil (endividadas, contas em atraso, sem condições de pagar) e estrato
  "até 10 s.m." como baixa renda.
- **SPA/MF:** apenas panoramas semestrais oficiais e SIGAP.
- **ESTBAN:** 10 municípios mais populosos da UF de maior exposição.

## Alternativas descartadas
- *Tópicos* do Trends (agregam sinônimos, mas o recorte muda sem aviso e dificulta
  reprodução) e nomes de marcas específicas (viés por patrocínio/publicidade).
- Sites de terceiros para dados da SPA/MF (fonte não oficial).
- `pytrends` (scraping, contra ADR 0001).

## Consequências
- Trends e EPAE são **proxies**; a monografia deve declarar que a seção CNAE R inclui
  atividades além de apostas e que o Trends mede interesse, não volume.
- Escolha de termos é decisão de pesquisa: mudar exige novo ADR.
