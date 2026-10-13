# Coleta das fontes sem API oficial

Cinco fontes exigem download manual. **Nada deve ser estimado, preenchido ou substituído**:
se um valor não estiver na fonte oficial, fica ausente. Data de corte: **31/12/2025**.
Período de todas as séries: **01/01/2020 a 31/12/2025** (EPAE só existe a partir de nov/2020).

Cada arquivo baixado deve ir para a pasta indicada, e a origem exata (link, data do download,
aba/célula) deve ser anotada em um `LEIA-ME_proveniencia.txt` na mesma pasta.

---

## 1. Google Trends — `data/raw/google_trends/`

**O que mede:** interesse relativo de busca (índice 0–100), *não* volume de apostas. Deve constar
na monografia como proxy de interesse, com essa limitação.

**Definições fixas (não alterar entre exportações):**
- Local: **Brasil**. Período: **01/01/2020 – 31/12/2025**. Categoria: **Todas as categorias**.
  Pesquisa: **Pesquisa na Web**.
- Termos (tipo *termo de pesquisa*, não "tópico"; digitar exatamente assim):
  1. `apostas online`  ← termo principal (usado no indicador composto)
  2. `bet`
  3. `jogo do tigrinho`
  Os dois últimos servem como análise de sensibilidade.

**Arquivos a exportar (botão ↓ em cada bloco):**
| # | Consulta | Bloco do Trends | Nome do arquivo |
|---|---|---|---|
| 1 | os 3 termos juntos (mesma escala) | Interesse ao longo do tempo | `temporal_BR_3termos.csv` |
| 2 | só `apostas online` | Interesse por sub-região (resolução: Região) | `regional_UF_apostas_online.csv` |
| 3 | só `bet` | Interesse por sub-região | `regional_UF_bet.csv` |
| 4 | só `jogo do tigrinho` | Interesse por sub-região | `regional_UF_jogo_do_tigrinho.csv` |

Observações: o Trends normaliza cada consulta para 0–100; por isso cada termo tem seu próprio
arquivo regional e o pipeline normaliza (min–max) antes de compor o indicador. Registre o
horário do download (os valores variam levemente entre coletas).

## 2. SPA/MF — `data/raw/spa_mf/`

Fonte oficial única: Panoramas semestrais da SPA e SIGAP
(https://www.gov.br/fazenda/pt-br/composicao/orgaos/secretaria-de-premios-e-apostas).
**Proibido usar sites de terceiros** ("Painel das Bets" etc.).

- Já transcrito: totais de 2025 (ver `spa_mf/LEIA-ME_proveniencia.txt`).
- Transcrever também, se existirem nos panoramas oficiais: **1º semestre/2025** e qualquer
  semestre anterior, para as variáveis `apostadores_cpf_unicos`, `ggr_valor`, `depositos_valor`.
- Formato: `data,variavel,valor` (data = último dia do período), anotando página do PDF.

## 3. EPAE — `data/raw/epae/`

Baixar o Excel em https://www.bcb.gov.br/estatisticas/tabelasespeciais → assunto **Moeda e
Crédito** (ou "Estatísticas de Meios de Pagamentos").

**Série a extrair:** fluxo mensal de **Pix de "Famílias" (pessoas físicas) → setor "Artes,
cultura, esporte e recreação" (CNAE seção R)**, valor em R$ e quantidade, nov/2020 a dez/2025.
Limitação a declarar: a seção R inclui a divisão de jogos de azar e apostas, mas também
esporte, cultura e recreação em geral — é um **proxy**, não medição direta de apostas.
Gravar `epae/epae_pix_recreacao.csv` (`data,valor`) e o arquivo original intacto ao lado.

## 4. PEIC — CNC — `data/raw/peic/`

https://pesquisascnc.com.br/pesquisa-peic/ (pode exigir cadastro gratuito).

**Séries (total Brasil, mensal, 2020–2025), gravar uma coluna `valor` por arquivo:**
- `peic_familias_endividadas.csv` — % de famílias endividadas
- `peic_contas_em_atraso.csv` — % com contas em atraso
- `peic_sem_condicoes_de_pagar.csv` — % que não terão condições de pagar

**Recorte de baixa renda:** usar o estrato *"até 10 salários mínimos"* da própria PEIC,
mesmas três séries, sufixo `_ate10sm`.

## 5. ESTBAN — BCB — `data/raw/estban/`

https://www.bcb.gov.br/estatisticas/estatisticabancariamunicipios

**Só depois** que o pipeline identificar a UF de maior exposição: baixar os arquivos mensais
dessa UF e filtrar os **10 municípios mais populosos da UF** (critério objetivo: população
estimada IBGE/SIDRA tabela 6579 nível município). Verbetes: operações de crédito e depósitos de
poupança (usar os nomes exatos que aparecem no arquivo). Gravar
`estban/estban_municipios.csv` (`data,municipio_ibge,variavel,valor`).

---

## Já coletado automaticamente
SGS/BCB, IBGE/SIDRA (séries nacionais) e Portal da Transparência (Novo Bolsa Família,
5.571 municípios, dez/2025) — ver `scripts/`.
