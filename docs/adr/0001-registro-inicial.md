# ADR 0001 — Decisões fundacionais do projeto

- **Status:** aceito
- **Data:** 2026-08-17

## Contexto

Ao estruturar o projeto a partir de `proposta-tcc-apostas-online.pdf`, várias decisões
técnicas não estavam explícitas na proposta e precisavam ser tomadas antes de
qualquer código ser escrito (ver `docs/00-proposta-resumo.md`, seção 12). Este ADR
registra as decisões tomadas em conjunto com o grupo em 2026-08-17.

## Decisões

### 1. Data de corte da base nacional: 31/12/2025

**Alternativas consideradas:**
- 31/12/2025 (fecha os três marcos regulatórios da proposta, incluindo a decisão do
  STF de dezembro/2025).
- Data mais recente disponível no momento da coleta de cada fonte (datas de corte
  distintas entre séries).

**Decisão:** 31/12/2025 para todas as fontes.

**Consequências:** simplifica comparabilidade entre séries e cobre integralmente o
período de interesse regulatório da proposta. Implica que dados posteriores a essa
data (se existirem no momento da coleta) devem ser truncados, não incorporados.

### 2. Trabalho em grupo (5+ integrantes)

**Decisão:** o TCC é produzido por um grupo de 5 ou mais pessoas.

**Consequências:** `CONTRIBUTING.md` define convenção de branches por módulo/tarefa
e exige revisão por dono de módulo antes de merge; `TASKS.md` é organizado por
módulo com campo de dono a preencher.

### 3. Painel interativo: Streamlit

**Alternativas consideradas:**
- Streamlit — Python puro, integra direto com o pipeline pandas/plotly existente.
- Dash/Plotly — mais controle de layout, curva de aprendizado maior.
- Power BI / Looker Studio — no-code, mas desacoplado do pipeline Python e da
  reprodutibilidade do projeto.

**Decisão:** Streamlit.

**Consequências:** `src/dashboard/app.py` consome diretamente `data/processed/`,
sem lógica de cálculo própria (spec 05). Dependência adicionada a `requirements.txt`.

### 4. Fontes sem API oficial estável: evitar scraping ao máximo

**Alternativas consideradas:**
- Aceitar scraping/bibliotecas não-oficiais livremente onde necessário.
- Evitar ao máximo, priorizando exportação manual oficial e, na ausência de
  alternativa, declarar a limitação e reduzir o escopo do indicador afetado em vez
  de depender de scraping frágil.

**Decisão:** evitar ao máximo (segunda opção).

**Consequências:** módulos de `src/data/` para Google Trends, painéis SPA/MF e
Portal da Transparência devem documentar explicitamente, no próprio docstring, a
ausência de alternativa e o plano de degradação, conforme
`specs/01-ingestao-dados/spec.md` critério 3 e `specs/constitution.md` §4. Pode
reduzir a granularidade/robustez do indicador territorial (Recortes 1 e 2), que a
proposta já trata como exploratório.

### 5. Rubrica de avaliação formal: inexistente no momento; ABNT NBR 14724 como fallback

**Decisão:** não há rubrica formal da UNIVESP disponível. Estrutura da monografia
segue ABNT NBR 14724 como padrão de fallback; critério de aderência usado é o
checklist cruzando entregáveis/objetivos do próprio PDF da proposta.

**Consequências:** se uma rubrica formal for disponibilizada futuramente, este ADR
deve ser revisado e `specs/constitution.md` §0 atualizado.

### 6. Prazo de entrega: ainda não definido

**Decisão:** seguir sem data-limite rígida em `TASKS.md` até que a instituição/
orientador defina o cronograma.

**Consequências:** revisar este ADR e `specs/constitution.md` §0 assim que houver
uma data de defesa/entrega definida.

## Como propor mudança a este ADR

Qualquer decisão acima que precise mudar (ex.: troca de data de corte, troca de
ferramenta de dashboard) deve ser feita via **novo ADR**, referenciando este, nunca
por edição silenciosa deste documento ou de `specs/constitution.md`.
