# Referências

Rastreamento de fontes de dados, papers e bibliotecas com metodologia relevante,
mantido desde o início do projeto (não só no fechamento). Formato final consolidado
conforme **ABNT NBR 6023** na versão final da monografia (spec 05, critério 4).

## Fontes de dados citadas na proposta

- BANCO CENTRAL DO BRASIL. **Sistema Gerenciador de Séries Temporais (SGS)**.
  Disponível em: https://www3.bcb.gov.br/sgspub. [referência completa a consolidar em ABNT]
  Séries usadas no núcleo nacional (`src/data/sgs.py`, ver
  `docs/adr/0002-series-sgs-nucleo-nacional.md`):
  - Série 29034 — Comprometimento de renda das famílias com o serviço da dívida com
    o SFN (ajuste sazonal). https://dadosabertos.bcb.gov.br/dataset/29034-comprometimento-de-renda-das-familias-com-o-servico-da-divida-com-o-sistema-financeiro-nacion
  - Série 29037 — Endividamento das famílias com o SFN em relação à renda acumulada
    dos últimos 12 meses. https://dadosabertos.bcb.gov.br/dataset/29037-endividamento-das-familias-com-o-sistema-financeiro-nacional-em-relacao-a-renda-acumulada-dos
  - Série 21084 — Inadimplência da carteira de crédito, pessoas físicas, total.
    https://dadosabertos.bcb.gov.br/dataset/21084-inadimplencia-da-carteira-de-credito---pessoas-fisicas---total
- BANCO CENTRAL DO BRASIL. **Estatísticas de Pagamentos por Atividade Econômica
  (EPAE)**. [referência completa a consolidar em ABNT]
- BANCO CENTRAL DO BRASIL. **Estatística Bancária Mensal (ESTBAN)**. [referência
  completa a consolidar em ABNT]
- CONFEDERAÇÃO NACIONAL DO COMÉRCIO DE BENS, SERVIÇOS E TURISMO (CNC). **Pesquisa de
  Endividamento e Inadimplência do Consumidor (PEIC)**. [referência completa a
  consolidar em ABNT]
- BRASIL. Secretaria de Prêmios e Apostas (SPA), Ministério da Fazenda. **Boletim
  semestral do mercado de apostas**, 1º semestre de 2025. [referência completa a
  consolidar em ABNT]
- COMITÊ NACIONAL DE SECRETÁRIOS DE FAZENDA (COMSEFAZ); CENTRO INTERNACIONAL CELSO
  FURTADO. **Boletim Fiscal dos Estados Brasileiros**, 3ª edição, ago. 2026.
  [referência completa a consolidar em ABNT]
- BANCO CENTRAL DO BRASIL. Estudo técnico sobre o mercado de apostas online e o
  perfil dos apostadores (Bolsa Família / Pix, ago. 2024). [referência completa a
  consolidar em ABNT]
- BRASIL. **Lei n.º 14.790, de 29 de dezembro de 2023**. Regulamentação do mercado de
  apostas de quota fixa.
- BRASIL. Ministério da Fazenda. **Portaria SPA/MF n.º 2.217/2025**.
- BRASIL. Ministério da Fazenda. **Instrução Normativa SPA/MF n.º 22/2025**.
- BRASIL. Supremo Tribunal Federal. Decisão de dezembro de 2025 sobre suspensão
  parcial das obrigações de bloqueio/encerramento de contas de apostas.
  [referência completa — número do processo a confirmar]
- IBGE. **Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua)**.
- IBGE. **Pesquisa Mensal de Comércio (PMC)**.
- IBGE. Estimativas populacionais.
- GOOGLE. **Google Trends**. Disponível em: https://trends.google.com.
- BRASIL. **Portal da Transparência**. Disponível em: https://portaldatransparencia.gov.br.
- BRASIL. **Cadastro Único para Programas Sociais (CadÚnico)**.

> Todas as referências acima precisam de complementação (autor institucional
> completo, URL de acesso específico, data de acesso) antes da consolidação final em
> ABNT NBR 6023 — ver `specs/05-relatorio-entrega/spec.md`, critério 4.

## Literatura acadêmica (Etapa 1 — revisão da literatura)

_(a preencher durante a revisão de literatura sobre jogos de azar e finanças
domiciliares — ver `TASKS.md`, seção "Fundamentação teórica")._

## Bibliotecas com metodologia relevante

| Biblioteca | Uso no projeto | Metodologia de referência |
|---|---|---|
| `ruptures` | Detecção de quebras estruturais (spec 02) | Truong, C.; Oudre, L.; Vayatis, N. **Selective review of offline change point detection methods**. Signal Processing, 2020. |
| `statsmodels` | Testes de estacionariedade, decomposição sazonal, SARIMAX | Documentação oficial: https://www.statsmodels.org |

> Completar esta tabela conforme cada biblioteca for de fato adotada (ver ADRs
> correspondentes em `docs/adr/`).
