# ADR 0003 — Estratégia de acesso por fonte de dados

- **Status:** aceito
- **Data:** 2026-08-17

## Contexto

`specs/constitution.md` §4 exige preferência estrita por API oficial e evitar
scraping ao máximo (decisão do grupo, ADR 0001). Ao implementar `src/data/`, cada uma
das 8 fontes da proposta (docs/00-proposta-resumo.md, seção 6) precisou ser
verificada individualmente — a disponibilidade real de API varia muito entre elas, e
assumir "todas têm API" por analogia com o SGS/BCB (ADR 0002) seria exatamente o tipo
de suposição não verificada que a constitution proíbe.

## Verificação feita (2026-08-17)

| Fonte | Acesso confirmado | Estratégia adotada |
|---|---|---|
| SGS/BCB | API REST pública estável, sem chave (`api.bcb.gov.br/dados/serie/...`) | Cliente HTTP direto — `src/data/sgs.py` (ADR 0002) |
| IBGE (PNAD Contínua, PMC, população) | API SIDRA pública estável, sem chave (`apisidra.ibge.gov.br`); tabelas 6381, 8880, 6579 testadas ao vivo | Cliente HTTP direto — `src/data/ibge.py` |
| Portal da Transparência / CadÚnico | API REST oficial documentada (OpenAPI real consultado), requer token gratuito por e-mail, endpoint `/api-de-dados/novo-bolsa-familia-por-municipio` (só por município, sem agregado nacional/UF nativo) | Cliente HTTP direto com token via `.env` — `src/data/transparencia.py` |
| Google Trends | Sem API pública, mas a própria interface oferece exportação CSV nativa (botão "Fazer download") — não é scraping, é um recurso oficial da ferramenta | Parser do CSV nativo (dois formatos: regional e temporal) — `src/data/google_trends.py`, **sem** `pytrends` |
| PEIC/CNC | Série histórica/microdados atrás de login em pesquisascnc.com.br; releases públicos são PDF mensal, não tabular | Exportação manual normalizada (arquivo colocado em `data/raw/peic/`) — `src/data/peic.py` |
| EPAE/BCB | Estatística nova (BCB começou a divulgar em out/2025); nenhum dataset/endpoint OData encontrado em dadosabertos.bcb.gov.br na verificação; divulgação só em caixa de texto do Relatório de Política Monetária (PDF) | Exportação manual normalizada — `src/data/epae.py` |
| Painéis semestrais SPA/MF | Sem API pública nem dataset aberto confirmado; painel/relatório semestral | Exportação manual normalizada (long-format, 3 variáveis) — `src/data/spa_mf.py` |
| ESTBAN/BCB | Existe no site institucional do BCB, mas nenhum padrão de URL de download estável foi confirmado com segurança na verificação | Exportação manual normalizada — `src/data/estban.py` |

## Decisão

Usar cliente HTTP direto apenas para as 3 fontes com API confirmada (SGS, IBGE/SIDRA,
Portal da Transparência). Para as demais 5, usar o padrão de **exportação manual
normalizada**: um integrante do grupo baixa o arquivo oficial (ou usa a função de
exportação nativa da ferramenta, no caso do Google Trends) e o coloca em `data/raw/
<fonte>/`, num formato de colunas documentado no docstring de cada módulo. Todos os
módulos de exportação manual compartilham a lógica de leitura/validação em
`src/data/_comum.py` (`ler_planilha_exportada`), exceto `google_trends.py` (formato
nativo específico, com dois layouts possíveis) e `spa_mf.py`/`estban.py` (arquivo já
long-format na origem, com múltiplas variáveis por linha).

## Consequências

- Nenhuma credencial hardcoded: o token do Portal da Transparência vem de
  `PORTAL_TRANSPARENCIA_TOKEN` (`.env`, ver `.env.example`).
- Os 5 módulos de exportação manual falham de forma explícita
  (`ArquivoExportacaoAusenteError`) se o arquivo não estiver em `data/raw/` — nunca
  retornam um DataFrame vazio silenciosamente.
- `TASKS.md` registra, para cada uma dessas 5 fontes, a tarefa de reconfirmar
  periodicamente se uma API oficial surgiu (especialmente EPAE, que é recente e pode
  ganhar dataset próprio) — se sim, o módulo correspondente deve ser reescrito para
  cliente HTTP direto, sem mudar o contrato de saída (`coletar(...) -> DataFrame`
  long-format já é o mesmo para os dois padrões).
- O indicador composto territorial (`src/features/indicador_territorial.py`, spec 02)
  deve tratar essas fontes manuais como tendo cadência de atualização mais lenta e
  potencialmente defasada em relação às fontes com API — isso já é consistente com a
  natureza "exploratória" do indicador territorial (constitution §5).
