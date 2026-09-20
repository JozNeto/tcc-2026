# Resultados — há sinais de prejuízo à renda das famílias mais pobres por causa de apostas online?

Todos os números vêm de dados coletados por API/fonte oficial (nada estimado), com data de
corte de 31/12/2025. Reproduzir: `python scripts/coletar_analise_central.py` e depois
`python scripts/analisar_pergunta_central.py` (saídas em `data/processed/` e `reports/figures/`).

## Resposta curta

**Os dados agregados disponíveis não permitem afirmar — nem descartar — prejuízo à renda das
famílias mais pobres causado por apostas.** O que a análise mostra:

1. **Onde há mais interesse por apostas, as famílias são mais pobres/dependentes de transferência**
   (associação forte, 27 UFs).
2. **Não há associação temporal detectável** entre o interesse por apostas e a piora posterior da
   inadimplência ou do comprometimento de renda no agregado nacional (72 meses).
3. **Nenhuma quebra estrutural** das séries de crédito coincide com os marcos regulatórios de 2025.

Critérios fixados **antes** de ver os resultados (constam no cabeçalho de
`scripts/analisar_pergunta_central.py`): C1 (série temporal) **não atendido**; C2 (corte transversal)
**atendido**; C3 (quebras nos marcos de 2025) **não atendido**.

## 1. Corte transversal, 27 UFs (C2)
Interesse de busca por apostas (Google Trends, 2020–2025) × dependência do Bolsa Família per capita
(Portal da Transparência, dez/2025) × rendimento do trabalho (PNAD, 4º tri/2025). Spearman, n = 27,
p ajustado por Bonferroni:

| Indicador de interesse | × Bolsa Família per capita | × Rendimento médio |
|---|---|---|
| "apostas online" | ρ = +0,78 (p < 0,001) | ρ = −0,69 (p = 0,0006) |
| "bet" | ρ = +0,83 (p < 0,001) | ρ = −0,62 (p = 0,004) |
| "jogo do tigrinho" | ρ = +0,09 (n.s.) | ρ = −0,16 (n.s.) |
| composto (média dos 3, min–máx) | ρ = +0,72 (p = 0,0002) | ρ = −0,59 (p = 0,010) |

UFs de maior interesse relativo (composto): AP (0,78), AC (0,70), PA (0,61), SE (0,56), MA (0,56),
AM (0,53), PE (0,50), PI (0,42). Figura: `reports/figures/fig2_uf_dispersao.png`.

## 2. Série temporal nacional, 2020–2025 (C1)
Variações mensais do crédito (inadimplência PF total, cartão rotativo, comprometimento de renda,
endividamento) regredidas no interesse de busca defasado 0–6 meses, com controles (Selic,
desocupação, rendimento real), erros robustos e p-valor conservador (o maior entre HAC e MQO),
Bonferroni sobre 28 testes por termo. **Nenhum teste significativo** para nenhum dos três termos
(menores p ajustados: 0,46 / 0,72 / 0,54); Granger sem significância após correção. O ganho de R²
do termo de apostas é pequeno (1–5%). Figura: `reports/figures/fig1_series_temporais.png`.

## 3. Quebras estruturais (C3)
Quebras detectadas (Pelt, sem informar as datas regulatórias): inadimplência PF total 06/2020,
07/2022 e **06/2025**; cartão rotativo 02/2022 e 05/2023; comprometimento 09/2021; endividamento
04/2021 e 09/2021; interesse por "apostas online" 02/2022, 05/2023 e 03/2024. Nenhuma a até 45
dias de 01/2025, 10/2025 ou 12/2025. A quebra de 06/2025 na inadimplência PF fica ~5 meses após a
regulamentação: sinal exploratório, não coincidência.

## 4. Dimensionamento (ordem de grandeza)
Perda líquida agregada dos apostadores (GGR 2025 = R$ 36,96 bi, SPA/MF) ÷ 25.245.319 CPFs únicos
que apostaram ÷ 12 = **R$ 122/mês por CPF único**. Isso equivale a **17,8%** do benefício médio do
Novo Bolsa Família (R$ 684,45/família, dez/2025) e **3,3%** do rendimento médio do trabalho
(R$ 3.743). É aritmética de média nacional: a SPA/MF não divulga por faixa de renda, e a média
não representa o gasto das famílias pobres (nem todo apostador aposta todo mês).

## Limitações (devem constar na monografia)
- **Sem microdados.** Associação agregada não prova causa nem prejuízo individual; o corte
  transversal por UF sofre de falácia ecológica.
- **Google Trends mede interesse de busca, não apostas**, via API não oficial (`pytrends`), com
  índice 0–100 relativo a cada consulta; valores variam levemente entre coletas.
- **72 observações mensais** e 4 séries de crédito só nacionais; a inadimplência por UF não existe
  na API do BCB.
- **Ausentes por não haver fonte acessível:** PEIC por faixa de renda (o dado que isolaria as
  famílias mais pobres), EPAE (Pix para recreação), séries semestrais da SPA/MF e ESTBAN
  (Recorte 2, municípios). Sem eles, a projeção de cenários condicionada à exposição e o
  Recorte 2 não foram executados.
- **Projeção univariada (`scripts/projetar_credito.py`).** SARIMAX de 24 meses por série, validado por
  origem móvel (h=12): nenhum modelo supera o naive de forma significativa (Diebold-Mariano, p entre 0,30 e
  0,97); os intervalos de 95% cobrem 59–86% no h=12; a projeção é plana e não é condicionada às apostas.
  Resultados em `data/processed/projecao_credito.{json,csv}` e `reports/figures/fig3_projecao.png`.
- A literatura com dados individuais encontra efeito (Baker et al., 2024, NBER 33108; BCB, Estudo
  Especial 119, 2024): nossos dados agregados são menos sensíveis e **não a contradizem**.
