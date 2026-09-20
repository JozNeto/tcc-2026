# Resumo da Proposta — TCC Ciência de Dados

> Fonte: `proposta-tcc-apostas-online.pdf` (raiz do projeto). Este resumo é derivado
> integralmente do PDF; qualquer informação não presente nele está marcada como
> **[AMBÍGUO/FALTANTE]** na seção 7.

## 1. Título e tema

**Apostas online e vulnerabilidade financeira das famílias brasileiras** —
mensuração nacional, quebras estruturais e projeção de cenários (2020–2029).

Títulos alternativos propostos:
- "Do Pix ao endividamento: análise preditiva do impacto das apostas online sobre a economia popular brasileira"
- "Apostas online no Brasil: integração de dados públicos, detecção de mudanças de regime e projeção do endividamento das famílias"

## 2. Problema de pesquisa

**Pergunta central:** qual a trajetória projetada dos indicadores de endividamento e
inadimplência das famílias brasileiras sob a manutenção do padrão atual de exposição
a apostas online?

**Perguntas operacionais:**
1. **Mensuração** — é possível construir, só com fontes públicas, um indicador nacional
   de exposição a apostas online consistente e reprodutível?
2. **Detecção** — as séries financeiras nacionais registram quebras estruturais, e
   coincidem com os marcos regulatórios de 2025?
3. **Projeção** — qual a trajetória esperada do endividamento em 24 meses, e qual a
   magnitude do custo de oportunidade patrimonial em horizontes mais longos?
4. **Distribuição territorial** — qual UF tem maior exposição relativa (indicador
   composto) e como essa exposição se distribui entre seus municípios?

**Fora de escopo (declarado explicitamente):** propostas de política pública,
avaliação de eficácia regulatória, relações causais em nível individual.

## 3. Unidade de análise e recortes

| Camada | Unidade | Função | Tratamento analítico |
|---|---|---|---|
| Núcleo | Brasil (nacional, séries mensais) | Objeto central | EDA completa, detecção de quebras, modelagem preditiva comparativa, projeção de cenários |
| Recorte 1 | 27 UFs | Identificar UF de maior exposição relativa | Indicador composto de exposição + ordenamento comparativo. **Sem projeção** |
| Recorte 2 | Municípios da UF identificada | Ilustrar heterogeneidade interna | Caracterização descritiva de um conjunto reduzido. **Sem modelagem** |

Limitação declarada: painéis da SPA/MF não abrem dados por UF/município — o indicador
territorial é uma **aproximação por fontes indiretas** (ex.: Google Trends), não uma
medição oficial.

## 4. Marcos regulatórios (usados para detecção de quebras estruturais)

| Marco | Data | Conteúdo |
|---|---|---|
| Regulamentação do mercado | jan/2025 | Exigência de autorização das operadoras (Lei 14.790/2023) |
| Restrição a beneficiários | out/2025 | Portaria SPA/MF 2.217/2025 e IN SPA/MF 22/2025 vedam participação de beneficiários do Bolsa Família e BPC |
| Suspensão parcial judicial | dez/2025 | STF suspende obrigações de bloqueio/encerramento de contas, mantendo vedação a novos cadastros |

## 5. Objetivos

**Geral:** construir base de dados integrada e modelos preditivos que descrevam a
evolução da exposição a apostas online e da vulnerabilidade financeira das famílias
brasileiras, projetando cenários.

**Específicos:**
- Integrar fontes públicas heterogêneas em base nacional mensal reprodutível.
- Construir e validar indicador de exposição a apostas online.
- Detectar quebras estruturais e confrontar com calendário regulatório.
- Comparar modelos de previsão de séries temporais sob validação temporal rigorosa.
- Projetar cenários e estimar custo de oportunidade patrimonial via simulação.
- Identificar UF de maior exposição relativa e ilustrar distribuição municipal.
- Publicar base, código e documentação sob princípios de dados abertos (FAIR).

## 6. Dataset(s) — fontes previstas (todas públicas, acesso programático)

| Fonte | Camada | Contribuição |
|---|---|---|
| SGS — Sistema Gerenciador de Séries Temporais (BCB) | Núcleo | Endividamento, comprometimento de renda, inadimplência PF |
| PEIC — Pesquisa de Endividamento e Inadimplência do Consumidor (CNC) | Núcleo | Único indicador mensal estratificado por faixa de renda |
| EPAE — Estatísticas de Pagamentos por Atividade Econômica (BCB) | Núcleo | Fluxo Pix de PF para setor de recreação (proxy de exposição) |
| Painéis semestrais SPA/MF | Núcleo | Nº apostadores, GGR, tíquete médio, perfil demográfico |
| Google Trends | Recortes 1 e 2 | Interesse relativo por UF/cidade — insumo principal do indicador composto territorial |
| Portal da Transparência / CadÚnico | Recortes 1 e 2 | Valores repassados e famílias beneficiárias |
| ESTBAN — Estatística Bancária Mensal (BCB) | Recorte 2 | Saldos de crédito/poupança (caracterização descritiva municipal) |
| IBGE (PNAD Contínua, PMC, estimativas populacionais) | Todas | Controles socioeconômicos, deflacionamento, normalização per capita |

Nenhum dataset já vem em arquivo — tudo é extraído via rotinas parametrizadas
(APIs/scraping de painéis públicos). Não há tamanho aproximado declarado.

## 7. Entregáveis obrigatórios

1. **Monografia** — fundamentação, metodologia, resultados, discussão.
2. **Base de dados integrada nacional** — publicada com identificador persistente e licença aberta.
3. **Pipeline reprodutível** — parametrizado por período, permitindo reconstrução/atualização futura por terceiros.
4. **Indicador de exposição a apostas** — metodologia documentada + versão territorial exploratória.
5. **Painel interativo** de consulta aos resultados.

Princípio explícito: publicação sob **FAIR** (localizável, acessível, interoperável, reutilizável).

## 8. Etapas do trabalho (conforme proposta)

1. Revisão da literatura e do marco regulatório.
2. Coleta e integração das fontes nacionais (rotinas em **Python**).
3. Tratamento e análise exploratória (deflacionamento IPCA, decomposição sazonal,
   testes de estacionariedade, tratamento de ausências/outliers, correlação cruzada com defasagens).
4. Detecção de quebras estruturais (algoritmos de segmentação, sem informação prévia
   das datas regulatórias — teste de validade externa).
5. Modelagem preditiva comparativa (escada de modelos: ingênuos → econométricos com
   exógenas → ML para séries únicas; validação por origem móvel/rolling origin;
   comparação por erro relativo + teste estatístico de diferença de desempenho).
6. Projeção de cenários (24 meses; 3 cenários: inercial, contenção, expansão; intervalos
   de predição explícitos) + simulação estocástica do custo de oportunidade patrimonial.
7. Recorte territorial ilustrativo (indicador composto por UF + caracterização descritiva
   de municípios da UF identificada).
8. Publicação e documentação (licença aberta, identificador persistente, repositório
   versionado, dicionário de dados, nota metodológica).

## 9. Restrições técnicas explícitas

- Linguagem: **Python** (mencionada explicitamente para as rotinas de extração; não há
  proibição explícita de outras linguagens, mas o restante do texto pressupõe stack Python/dados).
- Validação de modelos: **rolling origin** (validação temporal), não split aleatório —
  requisito metodológico explícito, dado que é série temporal.
- Reprodutibilidade e pipeline parametrizado por período são requisitos explícitos.
- Data de corte da base: a proposta recomenda **fixar antecipadamente** uma data de
  corte (dado que fontes oficiais têm divulgação intermitente/defasada) — mas não define qual.

## 10. Normas acadêmicas

- Citações: **ABNT NBR 6023** (mencionada explicitamente na nota de fontes).
- Nenhuma outra norma ABNT (ex.: NBR 14724 para estrutura de trabalhos acadêmicos) é
  citada explicitamente no PDF, embora seja prática padrão em TCCs brasileiros.

## 11. Riscos e delimitações assumidos (já declarados na proposta)

- Ausência de estatística oficial desagregada por UF/município (base do recorte
  territorial é indireta/exploratória, não medição oficial).
- Inferência apenas agregada — sem vínculo individual entre apostar e endividar-se.
- Séries de apostas cobrem período curto; combinadas com séries longas de
  endividamento como variável-resposta.
- Horizonte de projeção principal limitado a 24 meses; horizontes maiores são
  "exercício de cenário", não prev  isão.
- Cenário inercial pressupõe estabilidade regulatória — premissa frágil, declarada como condicional.
- Divulgação de dados setoriais é intermitente/defasada → recomenda-se fixar data de corte.

## 12. Pontos ambíguos ou faltantes na proposta [AÇÃO NECESSÁRIA]

Estes pontos **não estão definidos no PDF** e preciso da sua decisão antes de avançar
para a Etapa 1 (estrutura de diretórios) e specs:

1. **Rubrica de avaliação formal.** O PDF é a proposta de tema/projeto, não uma
   rubrica de banca/disciplina. Existe um documento separado (da UNIVESP ou do
   orientador) com os critérios de avaliação do TCC? Se sim, preciso dele para
   `specs/constitution.md` e para o checklist de aderência final.
2. **Prazo de entrega.** Não há data-limite no PDF. Qual o cronograma real (defesa,
   entregas parciais)?
3. **Data de corte da base de dados.** A proposta recomenda fixar uma data de corte,
   mas não escolhe uma. Proponho **31/12/2025** (fecha os três marcos regulatórios,
   incluindo a decisão do STF de dez/2025) — confirma ou prefere outra data?
4. **Ferramenta do "painel interativo".** Não especificada. Alternativas: Streamlit,
   Dash/Plotly, Power BI, Looker Studio. Tem preferência ou restrição institucional?
5. **Acesso programático às fontes.** Algumas fontes (Google Trends, painéis SPA/MF,
   Portal da Transparência) não têm API oficial estável — pode exigir scraping.
   Isso é aceitável, ou há restrição contra scraping?
6. **Chaves/credenciais de API.** SGS/BCB, IBGE (SIDRA), etc. costumam ser públicas
   sem chave, mas convém confirmar se você já tem acesso/cadastro em algum serviço
   (ex.: Google Trends via pytrends é não-oficial e instável).
7. **Formato/norma completa da monografia.** Só a norma de citação (ABNT NBR 6023) é
   citada. A UNIVESP costuma ter um template próprio (estrutura, capa, limite de
   páginas) — você tem esse template?
8. **Bibliotecas permitidas/proibidas.** Nenhuma restrição explícita. Vou assumir
   stack padrão de Ciência de Dados em Python (pandas, statsmodels, scikit-learn,
   ruptures/outra lib de detecção de quebras, etc.) salvo objeção.
9. **Trabalho individual ou em grupo.** O texto usa "o grupo" em alguns trechos
   ("responde a um objetivo explícito do grupo") — é um TCC em equipe? Isso afeta
   convenções de branch/commit em `CONTRIBUTING.md`.

**Não vou prosseguir para a Etapa 1 (estrutura de pastas, specs, MCP, TDD) até
recebermos suas respostas aos pontos acima** — especialmente 1, 2, 3 e 9, que
afetam diretamente `specs/constitution.md` e o TDD.
