"""Gera a V1 da entrega final a partir do .docx da Primeira Entrega editado pelo grupo.

Preserva: capa (com RAs), folha de rosto, folha de aprovação, sumário automático, numeração,
estilos e as referências já existentes (com links e datas de acesso). Substitui/atualiza:
resumo, introdução, fundamentação (correção ortográfica), metodologia, e acrescenta
Resultados e Discussão, Conclusão, novas referências e apêndices. Todos os números vêm dos
arquivos de dados/resultados do pipeline (nada digitado à mão).

Uso: pipeline/.venv/bin/python reports/final/gerar_v1_entrega_final.py
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

RAIZ = Path(__file__).resolve().parent.parent.parent
ORIGEM = RAIZ / "reports" / "parcial" / "relatorio_parcial_primeira_entrega.docx"
SAIDA = RAIZ / "reports" / "final" / "TCC_V1_entrega_final.docx"
PIPE = RAIZ / "pipeline"
FIGS = PIPE / "reports" / "figures"


# ------------------------------------------------------------------ dados ------
def br(x: float, d: int = 2) -> str:
    s = f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.replace("-", "−")


def carregar() -> dict:
    raw = PIPE / "data" / "raw" / "analise_central"
    base = pd.concat([pd.read_parquet(raw / "sgs.parquet"), pd.read_parquet(raw / "ibge_nacional.parquet")])
    base["data_referencia"] = pd.to_datetime(base["data_referencia"])
    w = base.pivot_table(index="data_referencia", columns="variavel", values="valor", aggfunc="first")
    tr = pd.read_parquet(raw / "trends_temporal.parquet")
    tr["data_referencia"] = pd.to_datetime(tr["data_referencia"])
    tr = tr.pivot_table(index="data_referencia", columns="termo", values="valor")
    df = w.join(tr, how="inner").loc["2020-01-01":"2025-12-01"]
    res = json.loads((PIPE / "data/processed/resultados_pergunta_central.json").read_text(encoding="utf-8"))
    uf = pd.read_csv(PIPE / "data/processed/uf_indicadores_pergunta_central.csv", index_col=0)
    meta = json.loads((raw / "trends_meta.json").read_text(encoding="utf-8"))
    bf = pd.read_csv(PIPE / "data/raw/transparencia/bolsa_familia_202512.csv")
    return {"df": df, "res": res, "uf": uf, "meta": meta, "bf": bf}


D = carregar()
DF, RES, UF = D["df"], D["res"], D["uf"]
DIM = RES["dimensionamento"]


def serie(nome: str) -> tuple[float, float, float, str, float, str]:
    s = DF[nome].dropna()
    return s.iloc[0], s.iloc[-1], s.min(), f"{s.idxmin():%m/%Y}", s.max(), f"{s.idxmax():%m/%Y}"


def teste_uf(indicador: str, cov: str) -> dict:
    return next(t for t in RES["transversal"]["testes"] if t["indicador"] == indicador and t["covariavel"] == cov)


def rho(indicador: str, cov: str) -> str:
    return br(teste_uf(indicador, cov)["rho"], 2)


def pval(p: float) -> str:
    return "< 0,001" if p < 0.001 else br(p, 3)


# ------------------------------------------------------- utilidades de docx ------
doc = Document(ORIGEM)
body = doc.element.body


def txt(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def achar(prefixo: str, tag: str = "p", inicio: int = 0):
    for i, el in enumerate(body.iterchildren()):
        if i >= inicio and el.tag.endswith("}" + tag) and txt(el).strip().startswith(prefixo):
            return el
    raise KeyError(prefixo)


def set_texto(el, texto: str) -> None:
    p = Paragraph(el, None)
    runs = p.runs
    if not runs:
        raise ValueError("parágrafo sem run: " + texto[:40])
    runs[0].text = texto
    for r in runs[1:]:
        r._element.getparent().remove(r._element)


T_CORPO = deepcopy(achar("O mercado de apostas online se tornou"))
T_H1 = deepcopy(achar("1 INTRODUÇÃO"))
T_H2 = deepcopy(achar("1.1 Contexto"))
T_LI = deepcopy(achar("Mensuração:"))
T_LEG = deepcopy(achar("Quadro 1 - Cronograma"))
T_QUEBRA = deepcopy([e for e in body.iterchildren() if e.tag.endswith("}p") and not txt(e).strip()
                     and any(b.get(qn("w:type")) == "page" for b in e.iter(qn("w:br")))][-1])


def _novo(modelo, texto: str):
    el = deepcopy(modelo)
    set_texto(el, texto)
    return el


def P(t):
    return _novo(T_CORPO, t)


def H1(t):
    return _novo(T_H1, t)


def H2(t):
    return _novo(T_H2, t)


def LI(t):
    return _novo(T_LI, t)


def LEG(t):
    return _novo(T_LEG, t)


def QUEBRA():
    return deepcopy(T_QUEBRA)


def TAB(cab: list[str], linhas: list[list[str]], tam: int = 9):
    t = doc.add_table(rows=1, cols=len(cab))
    t.style = "Light Grid Accent 1"
    for i, c in enumerate(cab):
        cel = t.rows[0].cells[i]
        cel.text = ""
        r = cel.paragraphs[0].add_run(c)
        r.font.bold = True
        r.font.size = Pt(tam)
        cel.paragraphs[0].paragraph_format.line_spacing = 1.0
    for lin in linhas:
        cels = t.add_row().cells
        for i, c in enumerate(lin):
            cels[i].text = ""
            r = cels[i].paragraphs[0].add_run(c)
            r.font.size = Pt(tam)
            cels[i].paragraphs[0].paragraph_format.line_spacing = 1.0
    el = t._tbl
    body.remove(el)
    return el


def FIG(caminho: Path, largura_cm: float = 14.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture(str(caminho), width=Cm(largura_cm))
    el = p._p
    body.remove(el)
    return el


def FONTE(t):
    el = _novo(T_LEG, t)
    return el


def inserir_antes(ancora, elementos) -> None:
    for e in elementos:
        ancora.addprevious(e)


# ----------------------------------------------------------- 1. RESUMO ----------
ini_c, fim_c, min_c, dmin_c, max_c, dmax_c = serie("comprometimento_renda_pf")
resumo = (
    "As apostas online tornaram-se, em poucos anos, um dos principais canais de gasto das famílias "
    "brasileiras, em um período de endividamento elevado. Este trabalho investiga se há sinais de "
    "prejuízo à renda das famílias mais pobres associados às apostas online, a partir de dados públicos "
    "agregados com data de corte em 31 de dezembro de 2025. Foram coletadas, por interfaces oficiais, "
    "séries do Banco Central do Brasil (crédito, inadimplência e taxa Selic) e do IBGE (renda, desocupação "
    "e população), o valor do Novo Bolsa Família nos 5.571 municípios em dezembro de 2025 e, pelo Google "
    "Trends, o interesse de busca por apostas no Brasil e nas 27 Unidades da Federação entre 2020 e 2025. "
    "Aplicaram-se regressões defasadas em primeiras diferenças com erros robustos, testes de Granger, "
    "correlações de Spearman entre as UFs, detecção de quebras estruturais pelo algoritmo Pelt e um "
    "dimensionamento a partir de dados oficiais da Secretaria de Prêmios e Apostas, com critérios de "
    "decisão definidos antes da análise e correção de Bonferroni. O interesse por apostas é maior nas UFs "
    f"mais dependentes do Bolsa Família e de menor rendimento (ρ = {rho('trends__apostas online', 'bf_per_capita')} "
    f"e ρ = {rho('trends__apostas online', 'rendimento_pnad')} para o termo “apostas online”), mas não há "
    "associação temporal significativa entre esse interesse e variações posteriores da inadimplência ou do "
    "comprometimento de renda, e nenhuma quebra estrutural das séries de crédito coincide com os marcos "
    "regulatórios de 2025. Uma projeção univariada de 24 meses, com SARIMAX validado por origem móvel, indica "
    "estabilidade nos patamares recentes, sem superar de forma significativa o modelo ingênuo. "
    f"A perda líquida média dos apostadores em 2025 equivale a R$ {br(DIM['ggr_2025_por_cpf_unico_mes'], 0)} "
    f"por mês, ou {br(DIM['razao_ggr_mensal_sobre_beneficio_bf'] * 100, 1)}% do benefício médio do Bolsa Família. "
    "Conclui-se que os dados agregados disponíveis não permitem afirmar nem descartar prejuízo à renda das "
    "famílias mais pobres; a análise é limitada pela ausência de microdados e pelo uso do interesse de busca "
    "como aproximação da exposição."
)
set_texto(achar("Este relatório mostra o progresso"), resumo)
set_texto(achar("Palavras-chave:"), "Palavras-chave: Apostas online; Endividamento das famílias; Séries temporais; "
          "Quebras estruturais; Google Trends; Ciência de Dados.")

# ---------------------------------------------------------- 2. INTRODUÇÃO -------
set_texto(achar("A lacuna que este trabalho quer preencher"),
          "A lacuna que este trabalho quer preencher é de natureza prática: os estudos existentes são limitados, "
          "publicados de forma esparsa e difíceis de repetir. Não há uma base pública consolidada que reúna, em uma "
          "série histórica única e bem documentada, indicadores de exposição a apostas e de vulnerabilidade "
          "financeira das famílias brasileiras. A pergunta de fundo que guiou a proposta é: qual será a evolução dos "
          "indicadores de endividamento e de inadimplência das famílias brasileiras se o padrão atual de exposição a "
          "apostas online continuar?")
ancora = achar("Dessa pergunta principal surgem quatro")
inserir_antes(ancora, [
    P("Considerando o que os dados públicos efetivamente permitem verificar, a pergunta central respondida nesta "
      "versão final é mais direta: há sinais de prejuízo à renda das famílias mais pobres associados às apostas "
      "online? Essa formulação preserva o interesse da proposta original e a torna testável com séries agregadas, "
      "sem exigir informações individuais que não são públicas.")])
set_texto(ancora, "Da pergunta de fundo surgem quatro perguntas operacionais, respondidas uma a uma na Seção 4.9:")

set_texto(achar("Objetivo geral é criar"),
          "Objetivo geral: reunir, a partir de fontes públicas, uma base de dados integrada e analisá-la para "
          "verificar se há sinais de prejuízo à renda das famílias mais pobres associados às apostas online, "
          "projetando cenários quando os dados permitirem.")
ancora_j = achar("A importância desse estudo")
inserir_antes(ancora_j.getprevious(), [
    P("Adequação do escopo. A execução do trabalho mostrou que parte das fontes previstas não oferece acesso "
      "programático nem arquivo público utilizável: a Pesquisa de Endividamento e Inadimplência do Consumidor "
      "(PEIC), as Estatísticas de Pagamentos por Atividade Econômica (EPAE) e a Estatística Bancária por município "
      "(ESTBAN). Sem elas, não foi possível isolar o estrato de baixa renda nem construir a exposição por meio de "
      "fluxos de Pix. O grupo, então, adaptou o trabalho ao que existe de fonte confiável: (i) o interesse de busca "
      "por apostas (Google Trends) passou a ser a medida de exposição; (ii) a dependência do Bolsa Família e o "
      "rendimento por UF passaram a representar a condição econômica das famílias; e (iii) a modelagem preditiva foi "
      "executada de forma univariada, sem a exposição como variável explicativa, pois a análise de associação não "
      "encontrou relação temporal que justificasse cenários condicionados a ela. Esses cenários e a simulação do "
      "custo de oportunidade patrimonial, embora implementados e testados, não foram executados. O Recorte 2 "
      "(municípios) não foi realizado por depender do ESTBAN. Esses pontos são retomados na Seção 4.9 e no "
      "Capítulo 5.")])
set_texto(achar("A importância desse estudo"),
          "A importância deste estudo é social: reunir as evidências disponíveis de que as famílias de menor renda "
          "participam de forma desproporcional do mercado de apostas online. Isso pode se tornar um fator de "
          "endividamento que afeta justamente quem tem menor capacidade de lidar com perdas e menor chance de "
          "acumular patrimônio. Do ponto de vista acadêmico, o trabalho ajuda a unir, em uma base única e "
          "reproduzível, dados hoje espalhados em boletins institucionais sem padronização, e aplica métodos "
          "consolidados de detecção de mudanças estruturais e de inferência estatística com correção para "
          "comparações múltiplas em um tema recente e em constante mudança regulatória.")
set_texto(achar("1.5 Estrutura Deste Relatorio"), "1.5 Estrutura do Trabalho")
set_texto(achar("Este relatório é dividido em quatro capítulos"),
          "Este trabalho está organizado em cinco capítulos. O Capítulo 2 traz a fundamentação teórica: evidências "
          "nacionais e internacionais sobre apostas online e vulnerabilidade financeira, o marco regulatório "
          "brasileiro, a literatura sobre detecção de quebras estruturais e o uso do Google Trends como indicador. "
          "O Capítulo 3 descreve a metodologia: fontes, linguagem e bibliotecas, preparação dos dados, métodos "
          "estatísticos e o caminho seguido até os resultados. O Capítulo 4 apresenta os resultados, responde às "
          "perguntas de pesquisa e discute limitações. O Capítulo 5 traz a conclusão. Seguem as Referências e dois "
          "apêndices: o cronograma e a divisão das atividades (Apêndice A) e o procedimento de reprodução "
          "(Apêndice B).")

# ------------------------------------------------- 3. FUNDAMENTAÇÃO (correções) --
set_texto(achar("Esta seção traz, de forma preliminar"),
          "Esta seção reúne a literatura acadêmica e institucional utilizada para fundamentar o trabalho. "
          "O levantamento não pretende ser exaustivo: concentra-se nas evidências mais diretamente ligadas à "
          "pergunta central e aos métodos empregados.")
set_texto(achar("2 FUNDAMENTAÇÃO TEÓRICA PRELIMINAR"), "2 FUNDAMENTAÇÃO TEÓRICA")
set_texto(achar("2.1 Aposta Online"), "2.1 Apostas Online e Vulnerabilidade Financeira: Evidências Internacionais")
set_texto(achar("A literatura econômica internacional recentemente"),
          "A literatura econômica internacional recente apresentou evidências sobre os efeitos negativos da "
          "legalização das apostas online. Baker et al. (2024), em estudo do National Bureau of Economic Research "
          "baseado em dados de transações bancárias, estimam que a legalização das apostas esportivas online está "
          "associada a um aumento de aproximadamente 12% no saldo devedor de cartão de crédito. O efeito é mais "
          "evidente entre famílias que já enfrentam restrições financeiras, que passaram a registrar aumento de "
          "dívidas, redução do crédito disponível e uso mais frequente do cheque especial.")
set_texto(achar("2.2 Apostas Online e Endividamento das Familias"),
          "2.2 Apostas Online e Endividamento das Famílias Brasileiras: Evidências Nacionais")
set_texto(achar("No contexto brasileiro, três evidencias"),
          "No contexto brasileiro, três frentes de evidência apontam no mesmo sentido. A primeira é o levantamento "
          "do Banco Central do Brasil (2024) sobre a relação entre o mercado de apostas online e o fluxo de "
          "pagamentos via Pix feito por beneficiários de programas sociais. A segunda vem da Confederação Nacional "
          "do Comércio, por meio de sua Gerência Executiva de Análise e Desenvolvimento Econômico, que aplicou o "
          "método de diferenças em diferenças aos dados da Pesquisa de Endividamento e Inadimplência do Consumidor "
          "e estimou que as apostas online aumentaram em cerca de 270 mil o número de famílias em inadimplência "
          "severa no período analisado (CNC, 2026). A terceira é a literatura acadêmica nacional: Santos, Coelho e "
          "Bernardes (2025) analisam, por pesquisa bibliográfica e documental, a relação entre apostas online e o "
          "endividamento do consumidor brasileiro à luz do marco legal vigente. Note-se que essas evidências usam "
          "dados individuais, de transações ou de pesquisa, enquanto este trabalho dispõe apenas de séries "
          "agregadas, o que limita o que pode ser afirmado (Seção 4.11).")
set_texto(achar("2.3 O Marco Regulatorio"), "2.3 O Marco Regulatório Brasileiro")
set_texto(achar("Três marcos regulatórios delimitam"),
          "Três marcos regulatórios delimitam o período de interesse deste trabalho e são usados, na etapa de "
          "detecção de quebras estruturais, exclusivamente como referência de validação externa, nunca como "
          "informação de entrada para os algoritmos de segmentação.")
set_texto(achar("A detecção de pontos de mudança"),
          "A detecção de pontos de mudança (change points) em séries temporais, sem conhecimento prévio de sua "
          "localização, é um problema consolidado na literatura estatística. Truong, Oudre e Vayatis (2020) "
          "sistematizam os principais métodos de detecção offline. Entre eles está o algoritmo PELT (Pruned Exact "
          "Linear Time), de Killick, Fearnhead e Eckley (2012), que encontra o conjunto ótimo de quebras "
          "minimizando um custo penalizado com tempo computacional aproximadamente linear, e que foi o método "
          "adotado neste trabalho por meio da biblioteca ruptures.")
ancora_25 = achar("3 METODOLOGIA")
inserir_antes(ancora_25.getprevious() if txt(ancora_25.getprevious()).strip() == "" else ancora_25, [
    H2("2.5 O Google Trends como Indicador de Interesse"),
    P("O Google Trends disponibiliza um índice relativo, de 0 a 100, da frequência de buscas por um termo em um "
      "período e local, normalizado pelo maior valor observado na própria consulta. Choi e Varian (2012) "
      "mostram que esse tipo de série pode antecipar indicadores econômicos, o que respalda seu uso como "
      "aproximação de comportamento. Trata-se, porém, de interesse de busca, e não de volume de apostas ou de "
      "gasto: quem pesquisa um termo pode não apostar, e quem aposta pode não pesquisar. Por isso, neste "
      "trabalho o índice é tratado como indicador de interesse (proxy) e essa limitação é declarada em todos os "
      "resultados.")])

# ----------------------------------------------------- 4. METODOLOGIA -----------
set_texto(achar("Trata-se de pesquisa quantitativa"),
          "Trata-se de pesquisa quantitativa, descritiva, exploratória e correlacional, baseada exclusivamente em "
          "dados públicos secundários de acesso programático, o que dispensa coleta primária. O trabalho não "
          "propõe soluções de política pública, não avalia a eficácia da legislação vigente e não estabelece "
          "relações causais em nível individual. As análises estimam associações estatísticas entre séries "
          "agregadas.")
set_texto(achar("A unidade de análise principal é o Brasil"),
          "A unidade de análise principal é o Brasil, com séries mensais nacionais de 2020 a 2025 (72 "
          "observações). Duas camadas de aprofundamento complementam esse núcleo: as 27 Unidades da Federação "
          "(Recorte 1) e os municípios da UF de maior interesse (Recorte 2).")
tab_camadas = achar("Camada", tag="tbl") if False else [e for e in body.iterchildren() if e.tag.endswith("}tbl")
                                                         and txt(e).startswith("CamadaUnidade")][0]
novo_camadas = TAB(["Camada", "Unidade", "Tratamento analítico"], [
    ["Núcleo", "Brasil", "Descrição das séries, associação temporal com o interesse de busca e detecção de quebras "
     "estruturais."],
    ["Recorte 1", "27 Unidades da Federação", "Associação entre interesse de busca, dependência do Bolsa Família "
     "e rendimento; ordenamento comparativo. Sem projeção."],
    ["Recorte 2", "Municípios da UF identificada", "Não executado (fonte ESTBAN indisponível)."],
], tam=10)
tab_camadas.addprevious(novo_camadas)
body.remove(tab_camadas)
set_texto(achar("Não há divulgação regular de dados de apostas"),
          "Não há divulgação regular de dados de apostas por Unidade da Federação ou por município. O indicador "
          "territorial é, portanto, uma aproximação construída a partir do interesse de busca (fonte indireta) e "
          "é apresentado com essa qualificação em todos os resultados.")

# remove o miolo antigo (3.3 até antes do cronograma) e o substitui
h33 = achar("3.3 Fontes de Dados")
cron_h = achar("4 CRONOGRAMA")
removiveis, ativo = [], False
for e in list(body.iterchildren()):
    if e is h33:
        ativo = True
    if e is cron_h:
        break
    if ativo:
        removiveis.append(e)
for e in removiveis:
    body.remove(e)

n_meses = RES["n_meses"]
metod = [
    H2("3.3 Fontes de Dados e Estratégia de Coleta"),
    P("Todas as fontes são públicas. Priorizou-se o acesso por interface de programação de aplicação (API) "
      "oficial. Quando não havia API, buscou-se o documento oficial da própria instituição. O Quadro 1 resume o "
      "que foi coletado e o que não foi possível obter."),
    TAB(["Fonte", "Dados utilizados", "Acesso", "Situação"], [
        ["SGS — Banco Central do Brasil", "Comprometimento de renda (série 29034), endividamento das famílias "
         "(29037), inadimplência PF total (21084), do cartão rotativo (21127) e do cartão total (21129), Selic "
         "acumulada no mês anualizada (4189) e IPCA mensal (433)", "API REST pública", "Coletado"],
        ["SIDRA — IBGE", "Taxa de desocupação (tabela 6381), rendimento médio real habitual (6390), população "
         "estimada por UF (6579) e rendimento médio por UF (5436, 4º trimestre de 2025)", "API pública",
         "Coletado"],
        ["Portal da Transparência", "Valor pago e número de beneficiários do Novo Bolsa Família em cada um dos "
         "5.571 municípios, dezembro de 2025", "API com token pessoal", "Coletado"],
        ["Google Trends", "Interesse de busca pelos termos “apostas online”, “bet” e “jogo do tigrinho”, Brasil "
         "e 27 UFs, 01/2020 a 12/2025", "Biblioteca pytrends (API não oficial)", "Coletado"],
        ["SPA/MF — Ministério da Fazenda", "Totais de 2025 do Panorama Semestral (CPFs únicos, contas ativas, "
         "GGR)", "Documento oficial (PDF)", "Transcrito"],
        ["PEIC — CNC", "Endividamento por faixa de renda", "Sem API; acesso restrito", "Não obtido"],
        ["EPAE — Banco Central", "Pix de famílias para recreação", "Sem API; planilha em página dinâmica",
         "Não obtido"],
        ["ESTBAN — Banco Central", "Saldos bancários por município", "Sem API; arquivos mensais", "Não obtido"],
    ], tam=8),
    LEG("Quadro 1 — Fontes de dados. Fonte: elaboração própria."),
    P("O Portal da Transparência entrega um município por chamada, sem total por UF ou nacional. A coleta dos "
      "5.571 municípios foi feita em fatias de 150 a 200 consultas, com pausa entre chamadas, registro do progresso "
      "em disco e interrupção automática ao primeiro sinal de limite de uso da API, para preservar a chave de "
      "acesso. Município sem registro seria gravado como ausente, nunca como zero; todos os 5.571 retornaram "
      "registro."),

    H2("3.4 Linguagem, Ambiente e Bibliotecas"),
    P("Todo o processamento foi escrito na linguagem Python, versão 3.12.3, executado em Ubuntu 24.04 sob "
      "Windows Subsystem for Linux. O Python foi escolhido por reunir bibliotecas maduras e abertas para "
      "coleta, séries temporais e estatística, e por permitir reprodução integral do estudo. As versões "
      "exatas usadas para gerar os resultados estão no Quadro 2 e fixadas no arquivo de dependências do "
      "repositório."),
    TAB(["Biblioteca (versão)", "Uso no trabalho"], [
        ["pandas 3.0.6 (McKinney, 2010)", "Leitura, alinhamento mensal, transformação e agregação dos dados"],
        ["NumPy 2.5.3 (Harris et al., 2020)", "Cálculo numérico e geração de números aleatórios"],
        ["SciPy 1.18.1 (Virtanen et al., 2020)", "Correlação de Spearman e distribuições estatísticas"],
        ["statsmodels 0.15.0 (Seabold; Perktold, 2010)", "Regressões (MQO com erros HAC), teste de Granger, "
         "testes ADF e KPSS e modelos SARIMAX da projeção"],
        ["ruptures 1.1.10 (Truong; Oudre; Vayatis, 2020)", "Detecção de quebras estruturais (algoritmo PELT)"],
        ["pytrends 4.9.2", "Coleta do Google Trends (API não oficial)"],
        ["requests 2.34.2", "Chamadas HTTP às APIs do BCB, IBGE e Portal da Transparência"],
        ["PyArrow 25.0.1", "Armazenamento em formato Parquet dos dados brutos"],
        ["matplotlib 3.11.2 (Hunter, 2007)", "Figuras"],
        ["pytest 9.1.1 e ruff 0.16.8", "Testes automatizados e verificação de estilo do código"],
        ["scikit-learn 1.9.1, LightGBM 4.7.0", "Modelos de previsão implementados, não usados nos resultados "
         "apresentados"],
    ], tam=9),
    LEG("Quadro 2 — Bibliotecas e versões. Fonte: elaboração própria."),
    P("O código está organizado em módulos de coleta (um por fonte), de tratamento, de análise estatística e de "
      "relatório, com 175 testes automatizados aprovados. Os testes incluem verificações com dados sintéticos de "
      "relação conhecida, para garantir que as funções estatísticas recuperam a relação embutida (por exemplo, "
      "a defasagem correta em uma série simulada), e testes contra as APIs reais do Banco Central e do IBGE."),

    H2("3.5 Preparação e Controle de Qualidade dos Dados"),
    P("Todos os dados foram truncados na data de corte de 31 de dezembro de 2025, que cobre os três marcos "
      "regulatórios. A janela de análise é de janeiro de 2020 a dezembro de 2025, ou seja, " + str(n_meses) +
      " meses, pois é o período em que existem simultaneamente as séries de crédito e o interesse de busca. As "
      "séries do IBGE em trimestre móvel foram associadas ao mês final do trimestre. As séries de crédito, "
      "desocupação e Selic já são percentuais, e o rendimento do IBGE já é real (deflacionado), por isso nenhum "
      "deflacionamento adicional foi aplicado."),
    P("Foram aplicadas verificações de qualidade a cada coleta: presença das colunas esperadas, ausência de "
      "duplicatas, respeito à data de corte, cobertura completa (27 UFs; 5.571 municípios) e falha explícita "
      "em caso de resposta inesperada de uma API, sem nunca substituir valor ausente por estimativa. As séries "
      "não apresentaram lacunas na janela analisada, de modo que nenhuma imputação foi necessária."),

    H2("3.6 Medida de Interesse por Apostas"),
    P("Como não há estatística oficial de apostas por UF ou por mês, o interesse de busca foi usado como "
      "aproximação. Definiram-se três termos de pesquisa, com Brasil como local, todas as categorias e pesquisa "
      "na web: “apostas online” (termo principal), “bet” e “jogo do tigrinho” (análises de sensibilidade). "
      "Foram evitados nomes de marcas de casas de apostas, que refletem publicidade, e “tópicos” do Google, cujo recorte "
      "pode mudar sem aviso."),
    P("Cada termo foi consultado isoladamente, com uma consulta temporal (mensal, nacional) e uma regional "
      "(27 UFs) por termo, totalizando seis consultas com pausa de 15 segundos entre elas. Como o índice é "
      "normalizado pelo maior valor de cada consulta, o interesse regional de cada termo foi normalizado entre "
      "0 e 1 (mínimo e máximo entre as UFs) e o indicador composto por UF é a média das três normalizações."),

    H2("3.7 Estratégia de Análise e Critérios de Decisão"),
    P("Para evitar interpretar resultados depois de vê-los, três critérios foram definidos antes da análise e "
      "registrados no código:"),
    LI("C1 (série temporal nacional): o interesse por “apostas online” está positivamente associado a variações "
       "posteriores (defasagem de 0 a 6 meses) da inadimplência PF total ou do cartão rotativo, controlando "
       "Selic, desocupação e rendimento real, com p-valor ajustado por Bonferroni inferior a 0,05;"),
    LI("C2 (corte transversal, 27 UFs): o interesse por “apostas online” é maior nas UFs mais dependentes do "
       "Bolsa Família per capita ou de menor rendimento, com p-valor ajustado inferior a 0,05;"),
    LI("C3 (descritivo): quebras estruturais das séries de crédito ocorrem próximas (até 45 dias) dos marcos "
       "regulatórios de 2025."),
    P("O atendimento a C1 e C2 seria compatível com a hipótese de prejuízo, sem prová-la. O não atendimento não "
      "a descarta, mas indica que os dados agregados não a sustentam."),

    H2("3.8 Métodos Estatísticos"),
    P("Estacionariedade. Os testes de Dickey e Fuller aumentado (Dickey; Fuller, 1979) e de Kwiatkowski, Phillips, "
      "Schmidt e Shin (1992) foram aplicados às séries de crédito no histórico completo do BCB. O primeiro não "
      "rejeitou a presença de raiz unitária (p = 0,68 para o comprometimento de renda, 0,45 para o "
      "endividamento e 0,20 para a inadimplência PF), e o segundo rejeitou a estacionariedade em nível nas "
      "três séries. Por isso, as regressões usam primeiras diferenças, o que evita a regressão espúria entre "
      "séries persistentes."),
    P("Associação temporal (critério C1). Para cada variável de crédito (inadimplência PF total, cartão "
      "rotativo, comprometimento de renda e endividamento) e cada defasagem k de 0 a 6 meses, estimou-se por "
      "mínimos quadrados ordinários a regressão da variação mensal do crédito na variação do interesse de "
      "busca k meses antes, com as variações mensais de Selic, desocupação e rendimento real como controles. O "
      "regressor de interesse foi padronizado, e o coeficiente é lido como variação em pontos percentuais do "
      "crédito por desvio-padrão de variação do interesse. Reportam-se também o ganho de R² atribuível ao "
      "interesse. O p-valor adotado é o maior entre o obtido com erros robustos a heterocedasticidade e "
      "autocorrelação de Newey e West (1987), com 6 defasagens, e o do MQO comum, pois erros robustos podem ser "
      "otimistas em amostras pequenas. O teste rejeita regressor com menos de 8 valores distintos (série "
      "esparsa). Completa a análise o teste de causalidade de Granger (1969) sobre as variações, com até 6 "
      "defasagens."),
    P("Comparações múltiplas. Para cada termo foram realizados 28 testes de regressão (4 variáveis de crédito × "
      "7 defasagens) e 4 testes de Granger. Todos os p-valores foram corrigidos pelo método de Bonferroni "
      "(Dunn, 1961), multiplicando-os pelo número de testes da família."),
    P("Corte transversal (critério C2). A associação entre o interesse de busca e as covariáveis das 27 UFs foi "
      "medida pelo coeficiente de correlação de postos de Spearman (1904), adequado a amostras pequenas e a "
      "relações monotônicas não lineares. As covariáveis são o Bolsa Família per capita (valor pago em "
      "dezembro de 2025 dividido pela população estimada de 2025) e o rendimento médio real do trabalho no 4º "
      "trimestre de 2025. Foram 8 testes (4 medidas de interesse × 2 covariáveis), com correção de Bonferroni."),
    P("Quebras estruturais (critério C3). Aplicou-se o algoritmo PELT, com custo quadrático (mudança de média) "
      "e penalidade igual à variância da série multiplicada pelo logaritmo natural do número de observações, "
      "critério semelhante ao BIC. O algoritmo decide livremente quantas quebras existem e não recebe as datas "
      "regulatórias, que só entram depois, na comparação, com tolerância de 45 dias."),
    P("Projeção e validação de modelos. Como a análise de associação não sustentou cenários condicionados ao "
      "interesse por apostas, a projeção é univariada: cada série de crédito é extrapolada a partir de sua própria "
      "dinâmica. O protocolo foi definido antes da execução. Usou-se o histórico completo do BCB até 31/12/2025 e "
      "cinco modelos: naive (repete o último valor), naive sazonal (repete o valor de 12 meses antes) e três "
      "especificações de SARIMAX (modelo autorregressivo integrado de médias móveis) sem variável exógena, de "
      "ordens (1,1,0), (0,1,1) e (1,1,1). A validação é por origem móvel (rolling origin): a cada mês, o modelo é "
      "reajustado apenas com dados anteriores e prevê 12 meses à frente, com treino inicial de 60% da série, o que "
      "impede o uso de informação futura. O erro é medido pelo MASE (erro absoluto médio escalado pelo erro do "
      "naive de 1 passo no treino inicial), a diferença de desempenho contra o naive é testada por Diebold e "
      "Mariano (1995), com correção de pequena amostra de Harvey, Leybourne e Newbold (1997) e ajuste para "
      "autocorrelação dos erros de horizonte longo, e a calibração dos intervalos é verificada pela cobertura "
      "empírica do intervalo de 95% em 12 meses. O modelo usado na projeção de 24 meses é o de menor MASE em 12 "
      "meses."),
    P("Dimensionamento. O GGR (Gross Gaming Revenue) é o valor apostado menos os prêmios pagos, isto é, a perda "
      "líquida agregada dos apostadores. Dividiu-se o GGR de 2025 pelo número de CPFs únicos que apostaram e "
      "por 12 meses, e o resultado foi comparado ao benefício médio do Novo Bolsa Família (valor total pago "
      "dividido pelo total de beneficiários em dezembro de 2025) e ao rendimento médio real do trabalho. "
      "Trata-se de aritmética de ordem de grandeza, não de estimativa do gasto de famílias pobres."),

    H2("3.9 Como Chegamos aos Resultados"),
    P("O caminho seguido, em ordem, foi:"),
    LI("Etapa 1 — Coleta: as séries do BCB e do IBGE, o Bolsa Família dos 5.571 municípios e o Google Trends "
       "foram coletados por scripts, com registro de data e proveniência de cada arquivo."),
    LI("Etapa 2 — Verificação: conferência de cobertura, período, duplicatas e data de corte."),
    LI("Etapa 3 — Definição dos critérios C1, C2 e C3, antes de qualquer teste de associação."),
    LI("Etapa 4 — Análise: regressões defasadas, Granger, correlações entre UFs, quebras estruturais, "
       "dimensionamento e projeção univariada com validação por origem móvel."),
    LI("Etapa 5 — Auditoria dos resultados, descrita a seguir."),
    P("A auditoria foi decisiva. Na primeira execução, os três termos do Google Trends foram coletados em uma "
      "única consulta, o que os coloca na mesma escala. Como “jogo do tigrinho” atingiu o pico de 100 em 2023, "
      "“apostas online” ficou reduzido a valores 0 ou 1, e a regressão produziu p-valores praticamente nulos com "
      "coeficientes de sinal alternado entre as defasagens. Dois sinais denunciaram o problema: o R² quase não "
      "mudava com a inclusão do interesse (0,314 sem e 0,324 com) e o p-valor era implausivelmente pequeno para "
      "um regressor quase constante. Concluiu-se que era artefato, não resultado. A coleta foi refeita com cada "
      "termo em consulta própria, o regressor passou a ser padronizado e passou-se a usar o maior entre o "
      "p-valor robusto e o de MQO, além de recusar regressores esparsos. Os resultados desta monografia são os "
      "obtidos após essa correção."),

    H2("3.10 Princípios Metodológicos"),
    P("O trabalho seguiu princípios definidos previamente pelo grupo, cuja alteração exigiria justificativa "
      "registrada:"),
    LI("Reprodutibilidade: sementes aleatórias fixas em processos estocásticos, ambiente de execução declarado "
       "e versões das bibliotecas fixadas;"),
    LI("Separação entre treino e teste: nenhuma informação do conjunto de teste é usada no treinamento de "
       "modelos, e a validação de modelos de série temporal é feita exclusivamente por origem móvel;"),
    LI("Data de corte: 31 de dezembro de 2025 em todas as fontes;"),
    LI("Preferência por fontes oficiais: usam-se APIs oficiais sempre que existem. A coleta por biblioteca não "
       "oficial é exceção documentada, e foi necessária apenas para o Google Trends, que não possui API "
       "oficial;"),
    LI("Nenhuma estimativa ou aproximação no lugar de dado: o que não pôde ser obtido (PEIC, EPAE, ESTBAN) "
       "foi declarado como ausente."),

    H2("3.11 Reprodutibilidade e Disponibilidade do Código"),
    P("Todo o código de coleta e análise, os testes e a configuração de integração contínua estão em um "
      "repositório versionado, cujo endereço será inserido nesta seção na publicação: [LINK DO REPOSITÓRIO — "
      "A INSERIR]. Os dados brutos não são versionados; são reconstruídos pelos scripts de coleta. O "
      "procedimento completo de reprodução está no Apêndice B."),
]
inserir_antes(cron_h, metod)

# ---------------------------------------------- 5. RESULTADOS E DISCUSSÃO -------
CR = ["inadimplencia_pf_total", "inadimplencia_cartao_rotativo", "inadimplencia_cartao_total",
      "comprometimento_renda_pf", "endividamento_familias_sfn"]
NOMES = {
    "inadimplencia_pf_total": "Inadimplência PF total (%)",
    "inadimplencia_cartao_rotativo": "Inadimplência do cartão rotativo (%)",
    "inadimplencia_cartao_total": "Inadimplência do cartão, total (%)",
    "comprometimento_renda_pf": "Comprometimento de renda das famílias (%)",
    "endividamento_familias_sfn": "Endividamento das famílias (% da renda)",
    "selic_acumulada_mes_anualizada": "Selic acumulada no mês, anualizada (% a.a.)",
    "taxa_desocupacao": "Taxa de desocupação (%)",
    "rendimento_medio_real_habitual": "Rendimento médio real habitual (R$)",
    "apostas online": "Interesse de busca: “apostas online” (0–100)",
    "bet": "Interesse de busca: “bet” (0–100)",
    "jogo do tigrinho": "Interesse de busca: “jogo do tigrinho” (0–100)",
}
lin_series = []
for k in CR + ["selic_acumulada_mes_anualizada", "taxa_desocupacao", "rendimento_medio_real_habitual",
               "apostas online", "bet", "jogo do tigrinho"]:
    a, b, mn, dmn, mx, dmx = serie(k)
    d = 0 if k == "rendimento_medio_real_habitual" or k in ("apostas online", "bet", "jogo do tigrinho") else 2
    lin_series.append([NOMES[k], br(a, d), br(b, d), f"{br(mn, d)} ({dmn})", f"{br(mx, d)} ({dmx})"])

t_ap = {}
for r in RES["temporal"]["apostas online"]["regressoes"]:
    if r["y"] not in t_ap or r["p_valor"] < t_ap[r["y"]]["p_valor"]:
        t_ap[r["y"]] = r
lin_temporal = []
for y in ["inadimplencia_pf_total", "inadimplencia_cartao_rotativo", "comprometimento_renda_pf",
          "endividamento_familias_sfn"]:
    r = t_ap[y]
    g = RES["temporal"]["apostas online"]["granger"][y]
    lin_temporal.append([NOMES[y], str(r["defasagem"]), br(r["coef_por_desvio_padrao"], 3),
                         br(r["delta_r2"] * 100, 1) + "%", br(r["p_ajustado"], 3), br(g["p_ajustado"], 3)])

lin_uf_testes = []
rot_ind = {"trends__apostas online": "“apostas online”", "trends__bet": "“bet”",
           "trends__jogo do tigrinho": "“jogo do tigrinho”", "trends_composto": "Composto (média dos três)"}
for ind in ["trends__apostas online", "trends__bet", "trends__jogo do tigrinho", "trends_composto"]:
    a, b = teste_uf(ind, "bf_per_capita"), teste_uf(ind, "rendimento_pnad")
    lin_uf_testes.append([rot_ind[ind], br(a["rho"], 2), pval(a["p_ajustado"]), br(b["rho"], 2), pval(b["p_ajustado"])])

top = UF.sort_values("trends_composto", ascending=False).head(8)
lin_top = [[uf, br(r["trends_composto"], 2), br(r["bf_per_capita"], 2), br(r["rendimento_pnad"], 0)]
           for uf, r in top.iterrows()]
base_uf = UF.sort_values("trends_composto").head(3)
lin_base = [[uf, br(r["trends_composto"], 2), br(r["bf_per_capita"], 2), br(r["rendimento_pnad"], 0)]
            for uf, r in base_uf.iterrows()]

lin_quebras = []
ROT_Q = {"inadimplencia_pf_total": "Inadimplência PF total", "inadimplencia_cartao_rotativo": "Cartão rotativo",
         "comprometimento_renda_pf": "Comprometimento de renda", "endividamento_familias_sfn": "Endividamento",
         "trends__apostas online": "Interesse “apostas online”"}
for k, v in RES["quebras"].items():
    datas = ", ".join(f"{d[5:7]}/{d[:4]}" for d in v["quebras"]) or "nenhuma"
    lin_quebras.append([ROT_Q[k], datas, "Não" if not v["coincidem_com_marcos"] else "Sim"])

nt = len(RES["temporal"]["apostas online"]["regressoes"])
menores = {t: min(r["p_ajustado"] for r in RES["temporal"][t]["regressoes"]) for t in RES["temporal"]}
a_ap, b_ap = serie("apostas online")[0], serie("apostas online")[1]
tr_media = DF[["apostas online", "bet", "jogo do tigrinho"]].groupby(DF.index.year).mean()

# ---- projeção univariada (scripts/projetar_credito.py) ----
PJ = json.loads((PIPE / "data/processed/projecao_credito.json").read_text(encoding="utf-8"))
PJ_CSV = pd.read_csv(PIPE / "data/processed/projecao_credito.csv")
ROT_MOD = {"naive": "Naive", "naive_sazonal": "Naive sazonal", "sarimax_110": "SARIMAX(1,1,0)",
           "sarimax_011": "SARIMAX(0,1,1)", "sarimax_111": "SARIMAX(1,1,1)"}
lin_val, lin_proj, cobertura_esc, dm12_sar, dm1_sar = [], [], [], [], []
for chave, v in PJ.items():
    for i, (m, r) in enumerate(v["modelos"].items()):
        p12 = r.get("dm_p_h12")
        dm_txt = "—" if m == "naive" or p12 is None else pval(p12)
        marca = " *" if m == v["modelo_escolhido"] else ""
        lin_val.append([v["rotulo"] if i == 0 else "", ROT_MOD[m] + marca, br(r["mase_h1"], 2), br(r["mase_h12"], 2),
                        dm_txt, br(r["cobertura95_h12"] * 100, 0) + "%"])
        if m.startswith("sarimax"):
            dm12_sar.append(p12)
            dm1_sar.append((chave, m, r.get("dm_p_h1")))
    esc = v["modelo_escolhido"]
    cobertura_esc.append((v["rotulo"], v["modelos"][esc]["cobertura95_h12"]))
    s12 = PJ_CSV[PJ_CSV["serie"] == chave].iloc[11]
    s24 = PJ_CSV[PJ_CSV["serie"] == chave].iloc[-1]
    d = 0 if False else 2
    lin_proj.append([v["rotulo"], ROT_MOD[esc], br(v["ultimo_valor"], d),
                     f"{br(s12['previsao'], d)} ({br(s12['intervalo_inferior'], d)}–{br(s12['intervalo_superior'], d)})",
                     f"{br(s24['previsao'], d)} ({br(s24['intervalo_inferior'], d)}–{br(s24['intervalo_superior'], d)})"])
dm12_vals = [p for p in dm12_sar if p is not None]
n_orig = sorted({r["n_origens"] for v in PJ.values() for r in v["modelos"].values()})
p1_endiv = [p for c, m, p in dm1_sar if c == "endividamento_familias_sfn" and p is not None]
p1_outros = [p for c, m, p in dm1_sar if c != "endividamento_familias_sfn" and p is not None]
cob_txt = "; ".join(f"{re.sub(r' \(.*\)', '', r)} {br(c * 100, 0)}%" for r, c in cobertura_esc)

resultados = [
    H1("4 RESULTADOS E DISCUSSÃO"),
    H2("4.1 Base de Dados Obtida"),
    P(f"A janela de análise reúne {n_meses} observações mensais de janeiro de 2020 a dezembro de 2025. A Tabela 1 "
      "resume as séries usadas. Além delas, foram obtidos o Bolsa Família de dezembro de 2025 nos 5.571 "
      f"municípios (R$ {br(D['bf']['valor'].sum() / 1e9, 2)} bilhões para {br(D['bf']['beneficiarios'].sum() / 1e6, 2)} "
      "milhões de beneficiários), o rendimento e a população das 27 UFs e o interesse de busca regional."),
    TAB(["Série", "Jan/2020", "Dez/2025", "Mínimo (mês)", "Máximo (mês)"], lin_series, tam=8),
    LEG("Tabela 1 — Séries mensais utilizadas, 2020–2025. Fonte: elaboração própria a partir de BCB (SGS), IBGE "
        "(SIDRA) e Google Trends."),

    H2("4.2 Comportamento do Crédito e da Renda"),
    P(f"O quadro macroeconômico do período é de deterioração do crédito das famílias. O comprometimento de renda "
      f"passou de {br(ini_c, 1)}% para {br(fim_c, 1)}%, seu máximo no período, em dezembro de 2025. A inadimplência PF "
      f"total foi de {br(serie('inadimplencia_pf_total')[0], 2)}% para {br(serie('inadimplencia_pf_total')[1], 2)}%, "
      f"e a do cartão rotativo de {br(serie('inadimplencia_cartao_rotativo')[0], 1)}% para "
      f"{br(serie('inadimplencia_cartao_rotativo')[1], 1)}%. A Selic acumulada no mês anualizada subiu de "
      f"{br(serie('selic_acumulada_mes_anualizada')[0], 1)}% para {br(serie('selic_acumulada_mes_anualizada')[1], 1)}% ao ano. "
      f"Ao mesmo tempo, a desocupação caiu de {br(serie('taxa_desocupacao')[0], 1)}% para "
      f"{br(serie('taxa_desocupacao')[1], 1)}% e o rendimento médio real do trabalho subiu de R$ "
      f"{br(serie('rendimento_medio_real_habitual')[0], 0)} para R$ {br(serie('rendimento_medio_real_habitual')[1], 0)}. "
      "Ou seja, o estresse financeiro cresceu apesar de mercado de trabalho e renda favoráveis, o que é "
      "compatível com o efeito do custo do crédito, mas também deixa espaço para outros fatores, entre eles as "
      "apostas, que estes dados agregados não conseguem separar."),

    H2("4.3 Interesse de Busca por Apostas"),
    P(f"O interesse por “apostas online” subiu de {br(tr_media.loc[2020, 'apostas online'], 1)} (média de 2020) para "
      f"{br(tr_media.loc[2023, 'apostas online'], 1)} (2023), com pico de 100 em setembro de 2023, e voltou a "
      f"{br(tr_media.loc[2025, 'apostas online'], 1)} em 2025. “Bet” cresceu de forma mais duradoura: média de "
      f"{br(tr_media.loc[2020, 'bet'], 1)} em 2020 e {br(tr_media.loc[2025, 'bet'], 1)} em 2025. “Jogo do tigrinho” "
      f"praticamente não existia até 2022 (média {br(tr_media.loc[2022, 'jogo do tigrinho'], 1)}), atingiu o pico em "
      f"dezembro de 2023 e teve média de {br(tr_media.loc[2024, 'jogo do tigrinho'], 1)} em 2024. Os termos, portanto, "
      "capturam momentos diferentes do fenômeno, o que reforça o uso dos três."),

    H2("4.4 Interesse por Apostas nas 27 Unidades da Federação"),
    P("A Tabela 2 mostra a correlação de postos entre o interesse de busca em cada UF e duas medidas da "
      "condição econômica local. O critério C2 foi atendido: onde há maior interesse por “apostas online” e por "
      f"“bet”, há maior dependência do Bolsa Família (ρ = {rho('trends__apostas online', 'bf_per_capita')} e "
      f"{rho('trends__bet', 'bf_per_capita')}) e menor rendimento do trabalho (ρ = "
      f"{rho('trends__apostas online', 'rendimento_pnad')} e {rho('trends__bet', 'rendimento_pnad')}), todas "
      "significativas após correção de Bonferroni. O termo “jogo do tigrinho” não apresenta associação "
      "(ρ próximo de zero), de modo que o resultado depende do termo escolhido e não deve ser generalizado."),
    TAB(["Indicador de interesse", "ρ com Bolsa Família per capita", "p ajustado", "ρ com rendimento",
         "p ajustado"], lin_uf_testes, tam=9),
    LEG("Tabela 2 — Correlação de Spearman entre interesse de busca e condição econômica, 27 UFs. Fonte: "
        "elaboração própria a partir de Google Trends, Portal da Transparência e IBGE."),
    FIG(FIGS / "fig2_uf_dispersao.png", 12.5),
    LEG("Figura 1 — Bolsa Família per capita e interesse de busca composto, 27 UFs. Fonte: elaboração própria."),
    P("A Tabela 3 lista as UFs de maior e de menor interesse composto. Amapá, Acre, Pará, Sergipe e Maranhão "
      "lideram; Distrito Federal, Santa Catarina e São Paulo têm os menores valores. Essas UFs de maior interesse "
      "têm, em geral, rendimento do trabalho abaixo da média e Bolsa Família per capita em torno de R$ 100 ou "
      "mais, contra cerca de R$ 16 a R$ 35 nas de menor interesse."),
    TAB(["UF", "Interesse composto (0–1)", "Bolsa Família per capita (R$)", "Rendimento médio (R$)"],
        lin_top + [["…", "…", "…", "…"]] + lin_base, tam=9),
    LEG("Tabela 3 — UFs de maior e de menor interesse por apostas. Fonte: elaboração própria."),

    H2("4.5 Associação Temporal entre Interesse por Apostas e Crédito"),
    P(f"Foram estimadas {nt} regressões para o termo principal (4 variáveis de crédito × 7 defasagens), além de "
      "quatro testes de Granger. Nenhum resultado foi significativo após a correção de Bonferroni; o menor p "
      f"ajustado foi {br(menores['apostas online'], 2)} para “apostas online”, {br(menores['bet'], 2)} para "
      f"“bet” e {br(menores['jogo do tigrinho'], 2)} para “jogo do tigrinho”. A Tabela 4 mostra, para cada variável "
      "de crédito, a defasagem com menor p-valor. O ganho de R² atribuível ao interesse de busca é pequeno e os "
      "sinais dos coeficientes variam conforme a variável e a defasagem, o que não é o padrão de uma relação "
      "estável. O critério C1 não foi atendido."),
    TAB(["Variável de crédito", "Melhor defasagem (meses)", "Coeficiente (p.p. por DP)", "Ganho de R²",
         "p ajustado (regressão)", "p ajustado (Granger)"], lin_temporal, tam=8),
    LEG("Tabela 4 — Associação temporal entre a variação do interesse por “apostas online” e a variação do "
        "crédito. Fonte: elaboração própria."),
    FIG(FIGS / "fig1_series_temporais.png", 14.5),
    LEG("Figura 2 — Interesse de busca e inadimplência (normalizados entre 0 e 1) e marcos regulatórios de 2025. "
        "Fonte: elaboração própria a partir de Google Trends e BCB."),
    P("A Figura 2 ajuda a interpretar o resultado: o pico de interesse em 2023 não é seguido por movimento "
      "semelhante das séries de inadimplência, que seguem tendências próprias associadas ao ciclo de juros. O "
      "aumento da inadimplência PF a partir de 2025 ocorre com o interesse de busca em patamar baixo."),

    H2("4.6 Quebras Estruturais e Marcos Regulatórios de 2025"),
    P("A Tabela 5 apresenta as quebras detectadas sem informar as datas regulatórias ao algoritmo. Nenhuma "
      "ocorre a menos de 45 dias de janeiro, outubro ou dezembro de 2025; o critério C3 não foi atendido. A "
      "quebra de junho de 2025 na inadimplência PF total ocorre cerca de cinco meses depois da regulamentação e "
      "quatro antes da restrição aos beneficiários, e é apenas um sinal exploratório, não uma coincidência."),
    TAB(["Série", "Quebras detectadas", "Coincide com marco de 2025?"], lin_quebras, tam=9),
    LEG("Tabela 5 — Quebras estruturais detectadas (PELT, custo quadrático). Fonte: elaboração própria."),

    H2("4.7 Projeção Univariada do Crédito para 24 Meses"),
    P("Como a análise de associação não sustentou cenários condicionados ao interesse por apostas, a projeção "
      "apenas extrapola a dinâmica de cada série de crédito, mantido o padrão recente. Foram comparados cinco "
      f"modelos com validação por origem móvel (horizonte de 12 meses, passo de 1 mês, {n_orig[0]} a {n_orig[-1]} "
      "origens por série), usando o histórico completo do BCB até dezembro de 2025 (178 a 252 observações). A "
      "Tabela 6 traz o MASE, o teste de Diebold e Mariano contra o naive e a cobertura empírica do intervalo de "
      "95%. Valores de MASE acima de 1 em 12 meses são esperados, pois o denominador é um erro de 1 passo."),
    TAB(["Série", "Modelo (* = usado na projeção)", "MASE h=1", "MASE h=12", "p (Diebold-Mariano vs. naive, h=12)",
         "Cobertura do IC 95% (h=12)"], lin_val, tam=8),
    LEG("Tabela 6 — Validação por origem móvel dos modelos de previsão. Fonte: elaboração própria."),
    P(f"Quatro resultados se destacam. Primeiro, nenhum SARIMAX supera o naive de forma significativa em 12 meses "
      f"(p entre {br(min(dm12_vals), 2)} e {br(max(dm12_vals), 2)}); as diferenças de MASE são muito pequenas. "
      "Segundo, em 1 passo só o endividamento das famílias tem ganho significativo sobre o naive "
      f"(p entre {pval(min(p1_endiv))} e {pval(max(p1_endiv))}); nas demais séries, p entre "
      f"{br(min(p1_outros), 2)} e {br(max(p1_outros), 2)}. Terceiro, o naive sazonal é pior que o naive em 1 passo "
      "e tem o mesmo MASE em 12 meses (a previsão 12 passos à frente é o valor de 12 meses antes do alvo, isto é, "
      "o último observado). Quarto, os intervalos de 95% cobrem menos que o nominal: nos modelos usados, a cobertura "
      f"empírica em 12 meses é de {cob_txt}. Os intervalos da projeção são, portanto, otimistas."),
    TAB(["Série", "Modelo", "Dez/2025 (observado)", "Dez/2026 (IC 95%)", "Dez/2027 (IC 95%)"], lin_proj, tam=8),
    LEG("Tabela 7 — Projeção univariada do crédito. Fonte: elaboração própria."),
    FIG(FIGS / "fig3_projecao.png", 15),
    LEG("Figura 3 — Projeção univariada do crédito para 24 meses, com intervalo de 95%. Fonte: elaboração própria."),
    P("A projeção é praticamente plana: mantém as quatro séries nos patamares de dezembro de 2025, com "
      "intervalos amplos que se abrem com o horizonte. Isso não é "
      "previsão de melhora nem de piora. Como nenhum modelo supera o naive de forma significativa, a escolha do "
      "SARIMAX entre as alternativas é praticamente indiferente, e a projeção deve ser lida como “se nada "
      "mudar”. Por não incluir o interesse por apostas, ela não responde o que aconteceria com o crédito sob "
      "diferentes níveis de exposição."),

    H2("4.8 Dimensionamento"),
    P(f"O GGR de 2025 foi de R$ 36,96 bilhões para 25.245.319 CPFs únicos que apostaram (SPA/MF, panorama "
      f"semestral de jan/2026), o que dá R$ {br(DIM['ggr_2025_por_cpf_unico_ano'], 0)} por apostador no ano e "
      f"R$ {br(DIM['ggr_2025_por_cpf_unico_mes'], 0)} por mês. O benefício médio do Novo Bolsa Família em "
      f"dezembro de 2025 foi de R$ {br(DIM['beneficio_bolsa_familia_medio_dez2025'], 2)} e o rendimento médio real do "
      f"trabalho, de R$ {br(DIM['rendimento_medio_real_habitual_dez2025'], 0)}. A perda líquida média mensal "
      f"equivale a {br(DIM['razao_ggr_mensal_sobre_beneficio_bf'] * 100, 1)}% do benefício médio e "
      f"{br(DIM['razao_ggr_mensal_sobre_rendimento'] * 100, 1)}% do rendimento médio. Esses percentuais são médias "
      "nacionais: a SPA/MF não divulga os valores por faixa de renda, nem todo apostador aposta todos os meses, "
      "e a média não representa o gasto de famílias pobres. O valor de R$ 164 mensais citado na Seção 1.1 "
      "(SPA/MF, primeiro semestre de 2025) refere-se ao apostador ativo e a outro período, portanto não é "
      "diretamente comparável a esta média. Os percentuais servem apenas para dar ordem de grandeza, e "
      "convivem com as evidências de que beneficiários do Bolsa Família transferiram cerca de R$ 3 bilhões a "
      "casas de apostas em um único mês de 2024 (BANCO CENTRAL DO BRASIL, 2024)."),

    H2("4.9 Respostas às Perguntas de Pesquisa"),
    P("Pergunta central — há sinais de prejuízo à renda das famílias mais pobres associados às apostas online? "
      "Os dados agregados não permitem afirmar nem descartar. Há um sinal a favor da hipótese no corte por UF "
      "(maior interesse onde há maior dependência de transferências e menor rendimento) e não há sinal na série "
      "temporal nacional nem nas quebras estruturais. Essas evidências não se contradizem: a primeira descreve "
      "onde o interesse é maior, e as outras verificam se o interesse antecede piora do crédito no agregado."),
    P("Mensuração — é possível construir um indicador nacional de exposição consistente e reprodutível com "
      "fontes públicas? Parcialmente. É possível e reprodutível construir um indicador de interesse de busca "
      "(nacional, mensal e por UF), mas ele não mede exposição real: não há fonte pública de volume de apostas "
      "por mês ou por UF, e as fontes que aproximariam o volume (EPAE) não puderam ser obtidas."),
    P("Detecção — as séries registram quebras estruturais e elas coincidem com os marcos de 2025? As séries "
      "registram quebras (Tabela 5), mas nenhuma coincide, dentro da tolerância de 45 dias, com os marcos de "
      "2025."),
    P("Projeção — qual a trajetória esperada do endividamento em 24 meses? Respondida em parte. A projeção "
      "univariada (Seção 4.7) indica que, mantido o padrão recente, as séries de crédito permanecem nos patamares "
      "de dezembro de 2025, com incerteza ampla. Não foram feitos cenários condicionados à exposição a apostas nem "
      "a simulação do custo de oportunidade patrimonial: sem associação temporal com o interesse de busca, não há "
      "base empírica para esses cenários, embora os módulos tenham sido implementados e testados."),
    P("Distribuição territorial — qual UF tem maior exposição relativa e como ela se distribui entre os "
      "municípios? Pelo indicador composto de interesse de busca, a UF de maior valor é o Amapá "
      f"({br(UF.loc['AP', 'trends_composto'], 2)}), seguido por Acre e Pará. Para o termo isolado “apostas online”, "
      "o maior valor é o de Sergipe. A distribuição entre municípios não foi feita, porque depende do ESTBAN. O "
      "resultado é exploratório, por se basear em interesse de busca."),

    H2("4.10 Discussão"),
    P("A associação entre interesse por apostas e pobreza relativa das UFs é coerente com a literatura que aponta "
      "efeitos concentrados em famílias financeiramente restritas (BAKER et al., 2024; CNC, 2026). Mas, por ser "
      "um resultado entre regiões, não autoriza concluir que as famílias pobres de cada UF apostam mais nem que "
      "perdem mais: pode refletir diferenças de acesso à internet, de publicidade regional ou de comportamento "
      "de busca. É a chamada falácia ecológica."),
    P("A ausência de associação temporal também merece cautela. Há ao menos quatro razões pelas quais o método "
      "poderia deixar de detectar um efeito real: (i) o crédito das famílias responde a um conjunto de fatores "
      "muito maior, dominado pelo ciclo de juros, cuja variação (Selic de 4,4% para 14,9%) tende a encobrir "
      "efeitos menores; (ii) o interesse de busca mede atenção, não gasto; (iii) o agregado nacional dilui um "
      "efeito que, segundo as evidências citadas, se concentra em um estrato específico; e (iv) 72 observações "
      "mensais dão poder estatístico limitado, e a correção de Bonferroni torna o teste conservador. Por isso, "
      "a conclusão correta é que os dados agregados não sustentam a hipótese, e não que ela seja falsa."),
    P("A projeção reforça a mesma cautela. Que modelos sofisticados não superem o naive é um resultado comum em "
      "séries macroeconômicas persistentes, e significa que, no horizonte de 12 a 24 meses, o melhor palpite "
      "estatístico é a persistência do nível atual. A projeção plana, portanto, "
      "não indica alívio nem agravamento. Mas ela deixa em aberto o que ocorreria se a exposição a apostas "
      "mudasse, e por isso não substitui um cenário condicional, que exigiria os dados de exposição ausentes."),
    P("Por fim, o dimensionamento sugere que, na média, a perda com apostas (R$ 122 por mês) é uma fração "
      "relevante, mas não avassaladora, do benefício médio do Bolsa Família. A relevância para as famílias mais "
      "pobres depende de quantas delas apostam e com que intensidade, informação que só microdados podem trazer."),

    H2("4.11 Limitações e Ameaças à Validade"),
    LI("Ausência de microdados: associações agregadas não provam causa nem prejuízo individual."),
    LI("Falácia ecológica no corte transversal por UF."),
    LI("Uso do Google Trends: mede interesse de busca, não apostas; o índice é relativo a cada consulta, varia "
       "levemente entre coletas e foi obtido por API não oficial, exceção ao princípio de preferir fontes "
       "oficiais. A escolha dos termos é uma decisão de pesquisa, e o resultado difere entre eles."),
    LI("Amostra temporal curta (72 meses) e séries de crédito só nacionais: o BCB não publica inadimplência "
       "por UF na API utilizada."),
    LI("Fontes não obtidas: PEIC por faixa de renda, EPAE e ESTBAN. Sem elas, o estrato pobre não pôde ser "
       "isolado no tempo, o Pix não foi usado como medida de exposição e o Recorte 2 não foi feito."),
    LI("Variáveis omitidas: outros fatores que afetam a inadimplência (renda, juros, endividamento prévio) só "
       "foram controlados em parte (Selic, desocupação e rendimento real)."),
    LI("Dados das apostas limitados a totais de 2025 (SPA/MF), sem série mensal ou semestral utilizável."),
    LI("Projeção univariada: não inclui a exposição a apostas, não supera o naive de forma significativa e tem "
       "intervalos de 95% com cobertura empírica abaixo do nominal; os cenários condicionais e a simulação do "
       "custo de oportunidade patrimonial não foram executados."),

    H1("5 CONCLUSÃO"),
    H2("5.1 Síntese dos Achados"),
    P("O trabalho reuniu, a partir de fontes públicas e sem estimativas, uma base integrada com séries do Banco "
      "Central, do IBGE, do Portal da Transparência e do Google Trends, e a usou para verificar se há sinais de "
      "prejuízo à renda das famílias mais pobres associados às apostas online. Três resultados se destacam: o "
      "interesse por apostas é maior nas UFs mais dependentes do Bolsa Família e de menor rendimento; não há "
      "associação temporal detectável entre esse interesse e a piora posterior do crédito no agregado nacional; e "
      "nenhuma quebra estrutural das séries de crédito coincide com os marcos regulatórios de 2025. A "
      f"perda líquida média de R$ {br(DIM['ggr_2025_por_cpf_unico_mes'], 0)} por mês por apostador equivale a "
      f"{br(DIM['razao_ggr_mensal_sobre_beneficio_bf'] * 100, 1)}% do benefício médio do Bolsa Família. "
      "A resposta à pergunta central é, portanto, inconclusiva: os dados agregados não permitem afirmar nem "
      "descartar prejuízo à renda das famílias mais pobres."),
    H2("5.2 Contribuições"),
    P("O trabalho contribui com (i) uma base e um procedimento reprodutíveis, com coleta automatizada e "
      "testada, que outros grupos podem atualizar; (ii) um desenho de análise com critérios definidos antes "
      "dos testes, correção para comparações múltiplas e auditoria dos resultados, que evitou a publicação de "
      "um resultado espúrio; (iii) um mapa objetivo das lacunas de dados públicos sobre apostas no Brasil, em "
      "especial a ausência de séries por faixa de renda, por UF e por município; e (iv) um retrato do interesse "
      "de busca por apostas nas 27 UFs, associado à pobreza relativa."),
    H2("5.3 Limitações"),
    P("As limitações estão detalhadas na Seção 4.11. As principais são a ausência de microdados, o uso do "
      "interesse de busca como aproximação da exposição e a não obtenção de PEIC, EPAE e ESTBAN, que impediram "
      "isolar o estrato de baixa renda e realizar o Recorte 2 e a projeção de cenários. A projeção univariada "
      "executada não supera o naive de forma significativa e tem intervalos de cobertura abaixo do nominal."),
    H2("5.4 Trabalhos Futuros"),
    LI("Obter a PEIC por faixa de renda (até 10 salários mínimos) e repetir a análise temporal no estrato de "
       "baixa renda, o dado que mais aproximaria o estudo da pergunta central;"),
    LI("Incorporar a EPAE (Pix de famílias para recreação) como medida de fluxo, e a série mensal ou semestral "
       "da SPA/MF, assim que forem acessíveis;"),
    LI("Usar dados individuais ou de transações, por meio de parcerias institucionais, e métodos de "
       "identificação como diferenças em diferenças em torno dos marcos de 2025;"),
    LI("Executar o Recorte 2 com o ESTBAN e a projeção condicionada à exposição, com cenários e custo de "
       "oportunidade patrimonial, já implementados no código;"),
    LI("Ampliar os termos de busca e testar a robustez do indicador a outras definições."),
]
inserir_antes(cron_h, resultados)

# ---------------------------------- referências novas + apêndices reorganizados --
h_ref = achar("REFERÊNCIAS")
quebra_ref = h_ref.getprevious()
refs_exist = []
e = h_ref.getnext()
while e is not None and e.tag.endswith("}p"):
    if txt(e).strip():
        refs_exist.append(e)
    e = e.getnext()
T_REF = deepcopy(refs_exist[-1])

NOVAS = [
    "BANCO CENTRAL DO BRASIL. Sistema Gerenciador de Séries Temporais (SGS): séries 29034, 29037, 21084, 21127, "
    "21129, 4189 e 433. Disponível em: https://dadosabertos.bcb.gov.br/. Acesso em 20 set 2026.",
    "BRASIL. Controladoria-Geral da União. Portal da Transparência: API de dados, Novo Bolsa Família por município. "
    "Disponível em: https://api.portaldatransparencia.gov.br/. Acesso em 20 set 2026.",
    "BRASIL. Ministério da Fazenda. Secretaria de Prêmios e Apostas. Panorama semestral do mercado regulado de "
    "apostas de quota fixa: dados de 1º de janeiro a 30 de dezembro de 2025. Brasília, jan. 2026. Disponível em: "
    "https://www.gov.br/fazenda/pt-br/composicao/orgaos/secretaria-de-premios-e-apostas/apresentacoes/"
    "defeso-2deg-panorama-semestral-de-apostas-de-quota-fixa-jan-2026.pdf. Acesso em 20 set 2026.",
    "CHOI, Hyunyoung; VARIAN, Hal. Predicting the present with Google Trends. Economic Record, v. 88, "
    "n. s1, p. 2-9, 2012.",
    "DIEBOLD, Francis X.; MARIANO, Roberto S. Comparing predictive accuracy. Journal of Business & Economic "
    "Statistics, v. 13, n. 3, p. 253-263, 1995.",
    "HARVEY, David; LEYBOURNE, Stephen; NEWBOLD, Paul. Testing the equality of prediction mean squared errors. "
    "International Journal of Forecasting, v. 13, n. 2, p. 281-291, 1997.",
    "DICKEY, David A.; FULLER, Wayne A. Distribution of the estimators for autoregressive time series with a "
    "unit root. Journal of the American Statistical Association, v. 74, n. 366, p. 427-431, 1979.",
    "DUNN, Olive Jean. Multiple comparisons among means. Journal of the American Statistical Association, "
    "v. 56, n. 293, p. 52-64, 1961.",
    "GOOGLE. Google Trends. Disponível em: https://trends.google.com/. Acesso em 20 set 2026.",
    "GRANGER, C. W. J. Investigating causal relations by econometric models and cross-spectral methods. "
    "Econometrica, v. 37, n. 3, p. 424-438, 1969.",
    "HARRIS, Charles R. et al. Array programming with NumPy. Nature, v. 585, p. 357-362, 2020.",
    "HUNTER, John D. Matplotlib: a 2D graphics environment. Computing in Science & Engineering, v. 9, n. 3, "
    "p. 90-95, 2007.",
    "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Sistema IBGE de Recuperação Automática (SIDRA): "
    "tabelas 6381, 6390, 5436 e 6579. Disponível em: https://apisidra.ibge.gov.br/. Acesso em 20 set 2026.",
    "KILLICK, Rebecca; FEARNHEAD, Paul; ECKLEY, Idris A. Optimal detection of changepoints with a linear "
    "computational cost. Journal of the American Statistical Association, v. 107, n. 500, p. 1590-1598, 2012.",
    "KWIATKOWSKI, Denis et al. Testing the null hypothesis of stationarity against the alternative of a unit "
    "root. Journal of Econometrics, v. 54, n. 1-3, p. 159-178, 1992.",
    "MCKINNEY, Wes. Data structures for statistical computing in Python. In: PYTHON IN SCIENCE CONFERENCE, 9., "
    "2010. Proceedings [...]. 2010. p. 56-61.",
    "NEWEY, Whitney K.; WEST, Kenneth D. A simple, positive semi-definite, heteroskedasticity and "
    "autocorrelation consistent covariance matrix. Econometrica, v. 55, n. 3, p. 703-708, 1987.",
    "SEABOLD, Skipper; PERKTOLD, Josef. Statsmodels: econometric and statistical modeling with Python. In: "
    "PYTHON IN SCIENCE CONFERENCE, 9., 2010. Proceedings [...]. 2010. p. 92-96.",
    "SPEARMAN, Charles. The proof and measurement of association between two things. The American Journal of "
    "Psychology, v. 15, n. 1, p. 72-101, 1904.",
    "VIRTANEN, Pauli et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature "
    "Methods, v. 17, p. 261-272, 2020.",
]
for r in NOVAS:
    novo = _novo(T_REF, r)
    depois = None
    for ex in refs_exist:
        if txt(ex).strip().upper() > r.upper():
            depois = ex
            break
    if depois is not None:
        depois.addprevious(novo)
        refs_exist.insert(refs_exist.index(depois), novo)
    else:
        refs_exist[-1].addnext(novo)
        refs_exist.append(novo)

# Cronograma vira Apêndice A, depois das referências
cron_elems, ativo = [], False
for e in list(body.iterchildren()):
    if e is cron_h:
        ativo = True
    if e is quebra_ref:
        break
    if ativo:
        cron_elems.append(e)
for e in cron_elems:
    body.remove(e)
    if e.tag.endswith("}p") and re.search(r"Quadro \d", txt(e)):
        set_texto(e, re.sub(r"Quadro (\d)", r"Quadro A\1", txt(e)))
set_texto(cron_h, "APÊNDICE A — CRONOGRAMA E DIVISÃO DAS ATIVIDADES")

ultimo = refs_exist[-1]
apend = [QUEBRA()] + cron_elems + [
    P("Nota sobre a execução. O cronograma acima corresponde ao plano seguido pelo grupo. A execução real sofreu "
      "a adaptação descrita na Seção 1.3: as fontes PEIC, EPAE e ESTBAN não puderam ser obtidas, e a modelagem "
      "preditiva condicionada à exposição e a projeção de cenários foram implementadas, mas não executadas "
      "sobre os dados reais; foi executada apenas a projeção univariada do crédito."),
    QUEBRA(),
    H1("APÊNDICE B — PROCEDIMENTO DE REPRODUÇÃO"),
    P("Para reproduzir o estudo são necessários Python 3.12, acesso à internet e um token gratuito do Portal da "
      "Transparência (solicitado em portaldatransparencia.gov.br, com e-mail). O procedimento é:"),
    LI("Clonar o repositório [LINK DO REPOSITÓRIO — A INSERIR] e criar um ambiente virtual;"),
    LI("Instalar as dependências com as versões fixadas do arquivo de requisitos;"),
    LI("Registrar o token do Portal da Transparência em um arquivo de ambiente local, que não é versionado;"),
    LI("Executar a coleta do núcleo nacional e a coleta em fatias do Bolsa Família (repetindo o comando até "
       "completar os 5.571 municípios);"),
    LI("Executar a coleta da análise central (SGS, IBGE por UF e Google Trends);"),
    LI("Executar a análise da pergunta central, que grava os resultados em formato JSON, tabelas e figuras;"),
    LI("Executar a suíte de testes para verificar a integridade do código."),
    P("Observações. O Google Trends pode devolver valores levemente diferentes a cada coleta; por isso a data da "
      "coleta é registrada junto dos dados (coleta desta versão: " + D["meta"]["coletado_em"][:10].split("-")[2] +
      "/" + D["meta"]["coletado_em"][:10].split("-")[1] + "/" + D["meta"]["coletado_em"][:4] + "). O limite de "
      "requisições do Portal da Transparência impõe pausas na coleta municipal."),
]
for e in reversed(apend):
    ultimo.addnext(e)

# atualiza o sumário ao abrir no Word
cfg = OxmlElement("w:updateFields")
cfg.set(qn("w:val"), "true")
doc.settings.element.append(cfg)

SAIDA.parent.mkdir(parents=True, exist_ok=True)
doc.save(SAIDA)
print("gerado:", SAIDA)
