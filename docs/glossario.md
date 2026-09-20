# Glossário

Nomes canônicos de variáveis e termos usados em todo o projeto (código, specs,
skills, monografia). Toda variável nova em `src/data/` ou `src/features/` deve ser
adicionada aqui antes de ser usada em mais de um módulo.

## Termos metodológicos

| Termo | Definição no contexto deste projeto |
|---|---|
| **Núcleo (nacional)** | Camada de análise principal do projeto — séries mensais do Brasil. Único nível com modelagem preditiva e projeção de cenários (ver `specs/constitution.md` §5). |
| **Recorte 1 (territorial — UF)** | Camada de aprofundamento sobre as 27 Unidades da Federação. Indicador composto de exposição + ordenamento comparativo. Sem projeção de cenários. |
| **Recorte 2 (territorial — município)** | Camada de aprofundamento sobre os municípios da UF identificada no Recorte 1. Caracterização descritiva. Sem modelagem. |
| **Data de corte** | Data-limite até a qual dados são incorporados à base, fixada em 31/12/2025 (ver `docs/adr/0001-registro-inicial.md`). |
| **Indicador composto de exposição** | Construção por aproximação (não estatística oficial direta) da exposição a apostas online por UF/município, a partir de fontes indiretas (principalmente Google Trends). Sempre rotulado como exploratório. |
| **Rolling origin / walk-forward** | Estratégia de validação de séries temporais em que o corte treino/teste avança no tempo a cada iteração, nunca embaralhando observações. Único método de validação permitido neste projeto (constitution §2). |
| **Cenário inercial** | Projeção assumindo manutenção das regras regulatórias vigentes. Rotulado como condicional, não como previsão incondicional. |
| **Exercício de cenário** (vs. previsão) | Rótulo obrigatório para qualquer projeção além do horizonte principal de 24 meses. |
| **GGR** | Gross Gaming Revenue — receita bruta de jogo das operadoras de apostas, métrica usada pela SPA/MF. |

## Variáveis (a preencher conforme `src/data/` for implementado)

| Nome canônico | Fonte | Unidade | Camada | Descrição |
|---|---|---|---|---|
| `comprometimento_renda_pf` | SGS/BCB (série 29034) | % | Núcleo | Comprometimento de renda das famílias com o serviço da dívida com o SFN, com ajuste sazonal. |
| `endividamento_familias_sfn` | SGS/BCB (série 29037) | % | Núcleo | Endividamento das famílias com o SFN em relação à renda acumulada dos últimos 12 meses. |
| `inadimplencia_pf` | SGS/BCB (série 21084) | % | Núcleo | Percentual da carteira de crédito de pessoas físicas com parcela em atraso superior a 90 dias. |
| `ipca_variacao_mensal` | SGS/BCB (série 433) | % | Núcleo | Variação mensal do IPCA; usado para construir o índice deflator em `src/features/tratamento.py`. |
| `taxa_desocupacao` | IBGE/SIDRA (tabela 6381) | % | Núcleo | Taxa de desocupação, PNAD Contínua, trimestre móvel. |
| `pmc_indice_volume_vendas_ajustado` | IBGE/SIDRA (tabela 8880) | número-índice (2022=100) | Núcleo | Índice de volume de vendas no comércio varejista, PMC, com ajuste sazonal. |
| `populacao_estimada` | IBGE/SIDRA (tabela 6579) | pessoas | Núcleo | População residente estimada, usada para normalização per capita. |
| `bolsa_familia_valor_repassado` | Portal da Transparência | R$ | Recortes 1 e 2 | Valor total repassado do Novo Bolsa Família, por município/mês. |
| `bolsa_familia_beneficiarios` | Portal da Transparência | pessoas | Recortes 1 e 2 | Quantidade de beneficiários do Novo Bolsa Família, por município/mês. |
| `google_trends_interesse_apostas` | Google Trends (exportação manual) | índice 0–100 | Recortes 1 e 2 | Interesse de busca relativo por "apostas online" (ou termo equivalente definido no indicador composto). |
| `percentual_familias_endividadas` | PEIC/CNC (exportação manual) | % | Núcleo | Percentual de famílias endividadas, indicador principal da PEIC. |
| `pix_pf_setor_recreacao_valor` | EPAE/BCB (exportação manual) | R$ | Núcleo | Fluxo de Pix de pessoas físicas para o setor "recreação" (CNAE), proxy de exposição a apostas. |
| `apostadores_qtd`, `ggr_valor`, `ticket_medio_valor` | SPA/MF (exportação manual) | pessoas / R$ / R$ | Núcleo | Número de apostadores ativos, receita bruta de jogo (GGR) e tíquete médio, por semestre. |
| `saldo_credito_pf`, `saldo_poupanca` | ESTBAN/BCB (exportação manual) | R$ | Recorte 2 | Saldos de crédito de pessoas físicas e de poupança, por município. |

> Ver `docs/adr/0002-series-sgs-nucleo-nacional.md` para a verificação e as
> alternativas descartadas na escolha destes três códigos SGS.

> Convenção: nomes de variáveis em `snake_case`, em português, sem acento (ex.:
> `comprometimento_renda_pf`, `pix_recreacao_valor`, `apostadores_ativos_qtd`).
