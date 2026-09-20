# ADR 0005 — Google Trends coletado via pytrends (exceção ao ADR 0001)

- **Status:** aceito (exceção documentada)
- **Data:** 2026-09-20

## Contexto
O ADR 0001 decidiu evitar scraping/bibliotecas não oficiais e o ADR 0004 previa exportação manual
do Google Trends. O grupo delegou a coleta e não há como automatizar o botão de download.
Sem o Trends não existe nenhuma série de exposição a apostas acessível por fonte aberta.

## Decisão
Usar `pytrends` (API não oficial) com poucas chamadas (1 temporal + 1 regional por termo,
pausa de 15 s), `retries=0` por incompatibilidade com urllib3 recente. Termos e período do
ADR 0004. **Cada termo em consulta própria**: consultar juntos comprimiu "apostas online" a 0/1
(escala dominada por "jogo do tigrinho") e gerou regressões espúrias, detectadas e descartadas.

## Consequências
- Coleta depende de endpoint não oficial e pode quebrar ou limitar; falha de forma explícita.
- Valores variam levemente entre coletas; registrar data (`trends_meta.json`).
- A monografia deve declarar a exceção e que o Trends mede interesse, não volume de apostas.
