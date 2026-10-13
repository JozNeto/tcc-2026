# Apostas online e vulnerabilidade financeira das famílias brasileiras

Pipeline de dados e análise do Trabalho de Conclusão de Curso (Bacharelado em
Ciência de Dados, UNIVESP) sobre a relação entre a expansão das apostas online e a
vulnerabilidade financeira das famílias brasileiras — mensuração nacional, detecção
de quebras estruturais associadas ao marco regulatório de 2025 e projeção
univariada das séries de crédito.

## Pergunta de pesquisa

Há prejuízo na renda das famílias mais pobres por causa de jogos e apostas online?
A análise usa apenas dados públicos agregados; os resultados e suas limitações
estão em [`RESULTADOS.md`](RESULTADOS.md).

## Estrutura do repositório

```
src/
  data/         rotinas de coleta, uma por fonte pública
  features/     tratamento (deflacionamento, imputação), diagnóstico exploratório,
                detecção de quebras estruturais, indicador territorial
  models/       modelos de previsão (naive, SARIMAX, aprendizado de máquina),
                validação por origem móvel, cenários, simulação de custo patrimonial
  evaluation/   métricas de erro e testes estatísticos de comparação de modelos
  reporting/    geração de figuras e proveniência
  dashboard/    painel interativo (Streamlit)
tests/          testes unitários, de integração, de qualidade de dados e harness
                de regressão de métricas entre execuções
data/           dados brutos/tratados (não versionados — ver .gitignore)
```

## Fontes de dados

| Fonte | Acesso | Módulo |
|---|---|---|
| SGS — Banco Central do Brasil | API pública, sem chave | `src/data/sgs.py` |
| IBGE — API SIDRA | API pública, sem chave | `src/data/ibge.py` |
| Portal da Transparência (Novo Bolsa Família) | API pública, requer token gratuito | `src/data/transparencia.py` |
| PEIC (CNC) | Exportação manual | `src/data/peic.py` |
| EPAE (BCB) | Exportação manual | `src/data/epae.py` |
| Painéis semestrais SPA/MF | Exportação manual | `src/data/spa_mf.py` |
| Google Trends | `pytrends` (API não oficial, exceção documentada) | `src/data/google_trends_api.py` |
| ESTBAN (BCB) | Exportação manual | `src/data/estban.py` |

Fontes "exportação manual" não têm API oficial estável — o arquivo correspondente
deve ser obtido manualmente e colocado em `data/raw/<fonte>/`, no formato descrito no
docstring de cada módulo em `src/data/`.

**Resultados e limitações da análise: ver [`RESULTADOS.md`](RESULTADOS.md).**

## Configuração

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # preencher PORTAL_TRANSPARENCIA_TOKEN
```

Token do Portal da Transparência: cadastre um e-mail em
https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email para recebê-lo
gratuitamente por e-mail. Cole o token recebido em `PORTAL_TRANSPARENCIA_TOKEN`, no
`.env`.

## Dados versionados por exceção

Por padrão `data/raw/` e `data/processed/` não são versionados (ver `.gitignore`) — são
reconstruídos pelos scripts de coleta. As únicas exceções são
`data/raw/transparencia/bolsa_familia_<mes>.csv` (progresso bruto por município) e
`data/processed/bolsa_familia_por_uf_<mes>.csv` (agregado de 27 linhas, uma por UF),
exigidos por `scripts/analisar_pergunta_central.py`. Nenhum dos dois tem dado pessoal — a
API do Portal da Transparência só expõe totais por município, não por CPF.

Eles são exceção porque são caros de refazer: a API entrega **um município por chamada**,
então reunir o Novo Bolsa Família exige consultar os 5.571 municípios do Brasil — com uma
chave pessoal, que tem limite de uso. Por isso essa coleta é feita à parte (não roda no
workflow `coleta-dados.yml`), em fatias pequenas e pausadas, de duas formas:

**Opção A — pelo GitHub Actions** (não precisa rodar nada local nem guardar o token na
sua máquina):

1. Cadastre o token como secret do repositório: **Settings → Secrets and variables →
   Actions → New repository secret**, nome `PORTAL_TRANSPARENCIA_TOKEN`, valor o token
   (ver "Configuração" acima para obtê-lo). Nunca cole o token em um Issue, PR ou commit.
2. Dispare o workflow **"Coleta do Bolsa Família por município (lenta, em fatias)"** na
   aba Actions ("Run workflow"). Ele roda em fatias até concluir os 5.571 municípios,
   commitando o progresso a cada fatia — se o job for interrompido (limite de tempo do
   runner, limite de uso da chave, instabilidade), é só disparar de novo: ele retoma de
   onde parou, sem perder o que já foi coletado. Ao concluir, o agregado por UF já fica
   commitado, pronto para o workflow `coleta-dados.yml`.

**Opção B — local:**

```bash
# 1) obtenha o token (ver seção "Configuração" acima) e coloque em pipeline/.env

# 2a) uma fatia por vez (retoma de onde parou a cada execução)
.venv/bin/python scripts/coletar_transparencia_fatias.py --mes 202512 --fatia 150 --pausa 1.5

# 2b) ou todas as fatias em sequência, com pausa entre elas, até concluir
#     (mes, fatia, pausa entre fatias em s, pausa entre requisições em s)
bash scripts/rodar_fatias_em_sequencia.sh 202512 150 180 1.5
```

O progresso fica em `data/raw/transparencia/bolsa_familia_<mes>.csv` (retomável — rodar de
novo continua de onde parou, nunca perde o que já foi coletado). Se a API sinalizar limite
de uso (HTTP 429/403), o script para sozinho; espere alguns minutos e rode de novo. Quando
os 5.571 municípios forem coletados, o script agrega por UF automaticamente e grava
`data/processed/bolsa_familia_por_uf_<mes>.csv`. Na opção B, **os dois arquivos precisam
ser commitados manualmente** (a opção A já faz isso sozinha):

```bash
git add data/raw/transparencia/bolsa_familia_*.csv data/processed/bolsa_familia_por_uf_*.csv
git commit -m "Atualiza coleta do Bolsa Família"
git push
```

Município sem registro na API nunca é gravado como zero, sempre como ausente.

## Testes

```bash
make test           # unitários + qualidade de dados + harness de regressão (sem rede)
make test-network   # integração contra as APIs reais (SGS, IBGE)
```

## Painel interativo

```bash
make dashboard
```

## Princípios do projeto

- Nenhum dado é aproximado, estimado informalmente ou substituído por valor
  fictício: toda série usada no trabalho vem de coleta real das fontes acima.
- Validação de modelos de série temporal exclusivamente por origem móvel (rolling
  origin) — nunca por divisão aleatória entre treino e teste.
- Toda simulação estocástica usa semente aleatória fixa e documentada.
- Indicadores territoriais (por Unidade da Federação e por município) são
  aproximações exploratórias construídas a partir de fontes indiretas — não são
  medição oficial, e são sempre apresentados com essa ressalva.
