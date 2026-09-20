# Spec — 05. Relatório, Dashboard e Publicação

> Cobre a **Etapa 1** (fundamentação teórica, parcialmente), a **Etapa 8**
> (publicação e documentação) e os entregáveis finais da proposta: monografia, base
> publicada, pipeline reprodutível, painel interativo.

## Objetivo

Produzir os entregáveis obrigatórios da proposta a partir dos artefatos gerados pelas
specs 01–04, garantindo publicação sob princípios FAIR e aderência ao checklist da
proposta.

## Escopo

1. **Geração de figuras/tabelas para a monografia** (`src/reporting/`): funções que
   consomem `data/processed/` e `reports/figures/` e produzem as figuras/tabelas
   finais em `reports/final/figuras/`, sem duplicar lógica de análise (que vive em
   `src/features/` e `src/models/` — este módulo só formata/plota o que já foi
   calculado).
2. **Painel interativo** (`src/dashboard/`): app Streamlit (decisão registrada em
   `specs/constitution.md` §7) que consome `data/processed/` diretamente — não
   recalcula análises, apenas visualiza resultados já produzidos pelo pipeline.
3. **Dicionário de dados e nota metodológica** (`docs/dicionario_dados.md`,
   `docs/nota_metodologica.md` — a criar nesta etapa): documentam cada coluna das
   bases publicadas e a metodologia de cada indicador, incluindo as ressalvas
   explícitas do indicador territorial (constitution §5).
4. **Checklist de aderência à proposta**: seção a preencher em
   `docs/00-proposta-resumo.md` (ou documento próprio) cruzando cada entregável/etapa
   da proposta contra o que foi de fato produzido.
5. **Referências** (`docs/referencias.md`): mantido ao longo de todo o projeto, não
   só nesta etapa — mas a consolidação final em formato ABNT NBR 6023 é
   responsabilidade desta spec.

## Critérios de aceite (Definition of Done)

1. O dashboard Streamlit roda localmente via `make dashboard` (a adicionar ao
   `Makefile`) e não contém nenhuma lógica de cálculo de indicador/modelo — só leitura
   de `data/processed/` e plotagem. Teste de fumaça (`tests/integration/test_dashboard_smoke.py`)
   garante que o app sobe sem erro com os dados de exemplo.
2. Toda figura em `reports/final/figuras/` tem proveniência rastreável: script que a
   gerou, versão da base usada (nome do arquivo em `data/processed/`), data de
   geração — via metadado embutido no nome do arquivo ou em `reports/final/figuras/manifesto.csv`.
3. `docs/dicionario_dados.md` cobre 100% das colunas presentes na base publicada
   final, incluindo, para as colunas territoriais, a ressalva de que são aproximações
   exploratórias, não medição oficial.
4. `docs/referencias.md` está formatado conforme ABNT NBR 6023 na versão consolidada
   final, e toda fonte de dado/biblioteca com metodologia relevante citada em
   qualquer spec ou ADR aparece ali.
5. Checklist de aderência preenchido cruzando cada item da seção "Entregáveis" e
   "Objetivos específicos" da proposta (ver `docs/00-proposta-resumo.md`, seções 5 e
   7) contra o artefato correspondente no repositório — nenhum item sem referência
   cruzada.
6. Base final publicada (fora do escopo de automação deste repo — ação manual em
   Zenodo ou similar) tem identificador persistente registrado em
   `docs/00-proposta-resumo.md` ou `README.md` assim que disponível.

## Contrato de dados

**Entrada:** todas as saídas de `data/processed/` das specs 01–04.

**Saída:** `reports/final/` (monografia + figuras), `docs/dicionario_dados.md`,
`docs/nota_metodologica.md`, `docs/referencias.md`, app rodável em `src/dashboard/app.py`.

## Casos de borda

- Resultado que contradiz a hipótese/expectativa inicial (ex.: nenhuma quebra
  estrutural coincide com marco regulatório): reportado como resultado válido no
  relatório, não omitido nem reinterpretado para "caber" na narrativa esperada.
- Dado indisponível na data de geração da monografia (fonte semestral cujo próximo
  corte cai depois do prazo do TCC): documentar explicitamente a defasagem no lugar
  de extrapolar sem aviso.

## Fora de escopo

- Cálculo de qualquer métrica, modelo ou indicador → specs 01–04. Esta spec só
  consome, formata, documenta e publica.
