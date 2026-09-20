# Spec — 01. Ingestão de Dados

> Cobre a **Etapa 2** da proposta ("Coleta e integração das fontes nacionais").
> Consulte `specs/constitution.md` (princípios 3 e 4: data de corte fixa, preferência
> estrita por API oficial) antes de implementar.

## Objetivo

Produzir rotinas parametrizadas em Python que extraem, das fontes públicas listadas
na proposta, uma base bruta por fonte, harmonizada em periodicidade, unidade
monetária e data de referência — sem ainda tratar ausências/outliers (isso é escopo
de `specs/02-limpeza-eda`).

## Escopo

| Fonte | Camada | Módulo de saída |
|---|---|---|
| SGS (BCB) | Núcleo | `src/data/sgs.py` |
| PEIC (CNC) | Núcleo | `src/data/peic.py` |
| EPAE (BCB) | Núcleo | `src/data/epae.py` |
| Painéis semestrais SPA/MF | Núcleo | `src/data/spa_mf.py` |
| Google Trends | Recortes 1 e 2 | `src/data/google_trends.py` |
| Portal da Transparência / CadÚnico | Recortes 1 e 2 | `src/data/transparencia.py` |
| ESTBAN (BCB) | Recorte 2 | `src/data/estban.py` |
| IBGE (PNAD Contínua, PMC, população) | Todas | `src/data/ibge.py` |

Cada módulo expõe uma função `coletar(data_corte: date, **kwargs) -> pd.DataFrame`
com contrato de saída documentado abaixo.

## Critérios de aceite (Definition of Done)

1. Cada módulo de coleta tem um teste de integração em `tests/integration/` que
   valida contra a fonte real (marcado `@pytest.mark.network`, não roda em `make test`
   padrão) e um teste unitário em `tests/unit/` que valida o parsing/harmonização
   contra uma resposta fixture gravada (sem rede).
2. Toda extração respeita a **data de corte 31/12/2025** (constitution §3): nenhum
   dado com data de referência posterior aparece na saída, salvo flag explícita
   `permitir_dados_pos_corte=False` documentada no docstring.
3. Toda fonte sem API oficial estável (Google Trends, painéis SPA/MF, Portal da
   Transparência quando aplicável) documenta no docstring do módulo: (a) por que não
   há alternativa sem scraping, (b) qual biblioteca/técnica não-oficial é usada, (c)
   qual o plano de degradação caso a fonte fique indisponível (constitution §4).
4. Cada `coletar()` grava metadados de proveniência junto à saída: fonte, URL/endpoint
   usado, timestamp da coleta, data de corte aplicada.
5. Saída de cada módulo passa nas checagens de `tests/data_quality/` referentes ao seu
   schema mínimo (ver contrato abaixo) antes de seguir para `src/features/`.
6. Nenhuma credencial é hardcoded — chaves/tokens (se necessários) vêm de variáveis de
   ambiente documentadas em `.env.example` (a criar quando a primeira fonte exigir).

## Contrato de dados (saída de cada `coletar()`)

DataFrame long-format, uma linha por (data de referência × unidade × variável):

| coluna | tipo | descrição |
|---|---|---|
| `data_referencia` | `date` | primeiro dia do mês/período de referência |
| `unidade` | `str` | `"BR"`, sigla de UF, ou código IBGE do município |
| `variavel` | `str` | nome canônico da variável (ver `docs/glossario.md`) |
| `valor` | `float` | valor bruto, sem deflacionar |
| `fonte` | `str` | identificador da fonte (ex.: `"SGS/BCB"`) |
| `coletado_em` | `datetime` | timestamp da execução da coleta |

## Casos de borda

- **Fonte fora do ar / rate limit:** a coleta deve falhar de forma explícita (exceção
  nomeada), nunca retornar silenciosamente um DataFrame vazio ou parcial sem log de
  aviso.
- **Mudança de schema na fonte:** teste unitário com fixture grava a resposta
  esperada; se a fonte mudar, o teste falha primeiro que o pipeline em produção.
- **Série com buraco temporal conhecido** (ex.: dado setorial de apostas só existe
  desde período recente, conforme delimitação da proposta): o módulo não preenche o
  buraco — retorna a série truncada e documenta o início real dos dados nos metadados
  de proveniência. Preenchimento é decisão de `specs/02-limpeza-eda`.
- **Google Trends normaliza por janela de consulta:** ao coletar séries de UFs/
  municípios diferentes, documentar explicitamente que os valores não são comparáveis
  entre consultas separadas sem uma âncora comum — tratar isso é responsabilidade do
  módulo `google_trends.py` (usar termo âncora comum entre consultas).

## Fora de escopo

- Deflacionamento, imputação, tratamento de outliers → `specs/02-limpeza-eda`.
- Construção do indicador composto territorial → `specs/02-limpeza-eda` (ver seção
  "Territorial" daquela spec).
