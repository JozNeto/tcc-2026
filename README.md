# Apostas online e vulnerabilidade financeira das famílias brasileiras

TCC de Ciência de Dados (UNIVESP) — mensuração nacional, quebras estruturais e
projeção de cenários (2020–2029) do endividamento das famílias brasileiras sob o
avanço das apostas online.

> Proposta completa: [`proposta-tcc-apostas-online.pdf`](proposta-tcc-apostas-online.pdf)
> Resumo estruturado: [`docs/00-proposta-resumo.md`](docs/00-proposta-resumo.md)

## Por que este projeto existe

Ver [`docs/00-proposta-resumo.md`](docs/00-proposta-resumo.md) para a pergunta de
pesquisa completa, objetivos e delimitações. Em resumo: construir uma base nacional
mensal reprodutível cruzando indicadores de exposição a apostas online (Pix, GGR,
tíquete médio) com indicadores de endividamento/inadimplência das famílias, detectar
se os marcos regulatórios de 2025 coincidem com quebras estruturais nas séries, e
projetar cenários de endividamento em 24 meses.

## Como este repositório é organizado

Este projeto segue **spec-driven development**: nenhum código em `src/` existe sem
uma spec aprovada em `specs/`. Os princípios inegociáveis (reprodutibilidade, sem
vazamento de dados, escopo por camada, validação por origem móvel) estão em
[`specs/constitution.md`](specs/constitution.md) — leia antes de contribuir.

```
docs/           documentação viva: resumo da proposta, TDD, ADRs, glossário, referências
specs/          especificações por módulo (spec-driven development) + constitution.md
.mcp/           servidor MCP local + skills que padronizam como cada etapa é feita
src/            código de produção (ingestão, features, modelos, avaliação, relatório, dashboard)
tests/          testes unitários, integração, qualidade de dados, harness de comparação de modelos
notebooks/      exploração ad-hoc (não é fonte da verdade — o pipeline em src/ é)
data/           raw/interim/processed (git-ignored; ver docs/tdd.md para como reconstruir)
reports/        figuras e monografia final
TASKS.md        plano de execução derivado das specs, com status
```

## Setup local

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make test                   # roda o harness completo (dados + unit + integração)
```

## Fluxo de trabalho

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) para convenção de commits e branches (grupo
de 5+ integrantes), e [`TASKS.md`](TASKS.md) para o plano de execução atual.

## Status

Projeto em fase de estruturação inicial (specs e TDD). Ver `TASKS.md` para o estado
detalhado de cada etapa da proposta.
