"""Gera reports/final/cronograma_tcc.docx — capítulo de cronograma isolado, para
inserção na monografia.

Diferença deliberada em relação a docs/cronograma_equipe.md (documento de gestão
interna do projeto): este arquivo é redigido em registro acadêmico, sem menções a
arquivos de código-fonte, caminhos de módulo ou nomes de arquivo — apenas às
atividades de pesquisa, como esperado em um documento voltado à avaliação
acadêmica. A fonte de verdade sobre "quem faz o quê tecnicamente" continua sendo
docs/cronograma_equipe.md; este documento é a tradução acadêmica do mesmo plano.

Uso: `python3 reports/final/gerar_cronograma.py`
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

SAIDA = Path(__file__).resolve().parent / "cronograma_tcc.docx"


def configurar_documento(doc: Document) -> None:
    estilo_normal = doc.styles["Normal"]
    estilo_normal.font.name = "Times New Roman"
    estilo_normal.font.size = Pt(12)
    rpr = estilo_normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), "Times New Roman")

    fmt = estilo_normal.paragraph_format
    fmt.line_spacing = 1.5
    fmt.space_after = Pt(0)

    for secao in doc.sections:
        secao.top_margin = Cm(3)
        secao.left_margin = Cm(3)
        secao.bottom_margin = Cm(2)
        secao.right_margin = Cm(2)


def paragrafo(doc, texto="", *, tamanho=12, negrito=False, italico=False,
              alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, espacamento_simples=False,
              recuo_primeira_linha=None):
    p = doc.add_paragraph()
    p.alignment = alinhamento
    if espacamento_simples:
        p.paragraph_format.line_spacing = 1.0
    if recuo_primeira_linha is not None:
        p.paragraph_format.first_line_indent = Cm(recuo_primeira_linha)
    if texto:
        run = p.add_run(texto)
        run.font.size = Pt(tamanho)
        run.font.bold = negrito
        run.font.italic = italico
    return p


def titulo_capitulo(doc, texto: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(texto.upper())
    run.font.bold = True
    run.font.size = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    return p


def subtitulo(doc, texto: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(texto)
    run.font.bold = True
    run.font.size = Pt(12)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    return p


def legenda(doc, texto: str):
    paragrafo(doc, texto, tamanho=10, espacamento_simples=True, alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(12)


def tabela_simples(doc, cabecalho: list[str], linhas: list[list[str]]):
    tabela = doc.add_table(rows=1, cols=len(cabecalho))
    tabela.style = "Light Grid Accent 1"
    for i, texto in enumerate(cabecalho):
        celula = tabela.rows[0].cells[i]
        celula.text = ""
        run = celula.paragraphs[0].add_run(texto)
        run.font.bold = True
        run.font.size = Pt(10)
    for linha in linhas:
        cels = tabela.add_row().cells
        for i, texto in enumerate(linha):
            cels[i].text = ""
            run = cels[i].paragraphs[0].add_run(texto)
            run.font.size = Pt(10)
    doc.add_paragraph()
    return tabela


def main():
    doc = Document()
    configurar_documento(doc)

    titulo_capitulo(doc, "CRONOGRAMA")
    paragrafo(doc, (
        "O cronograma institucional organiza o Trabalho de Conclusão de Curso em "
        "três entregas quinzenais, apresentadas no Quadro 1."
    ), recuo_primeira_linha=1.25)
    tabela_simples(
        doc,
        ["Entrega", "Início da quinzena", "Vencimento", "Carência"],
        [
            ["Primeira Entrega", "24/08/2026 (Quinzena 2)", "01/09/2026, 23:59", "06/09/2026, 23:59"],
            ["Segunda Entrega", "05/10/2026 (Quinzena 5)", "13/10/2026, 23:59", "18/10/2026, 23:59"],
            ["Entrega Final", "02/11/2026 (Quinzena 7)", "10/11/2026, 23:59", "15/11/2026, 23:59"],
        ],
    )
    legenda(doc, "Quadro 1 — Cronograma institucional de entregas.")

    paragrafo(doc, (
        "As atividades de pesquisa foram distribuídas entre os oito integrantes "
        "do grupo, cada um responsável por uma frente de trabalho principal, "
        "conforme apresentado no Quadro 2. A divisão busca cobrir, de forma "
        "equilibrada, as etapas metodológicas descritas no capítulo anterior: "
        "coleta de dados, tratamento e análise exploratória, detecção de quebras "
        "estruturais, modelagem preditiva, avaliação estatística, projeção de "
        "cenários e consolidação dos resultados."
    ), recuo_primeira_linha=1.25)
    tabela_simples(
        doc,
        ["Integrante", "Frente de trabalho principal"],
        [
            ["Fabiano Guilherme Dionizio Bortolussi", "Coleta de dados de fontes públicas com interface de "
             "programação de aplicação oficial (Banco Central do Brasil, IBGE, Portal da Transparência)."],
            ["José Araújo Neto", "Coleta de dados de fontes sem interface de programação de aplicação oficial "
             "estável, por meio de exportação manual documentada (PEIC, EPAE, painéis da Secretaria de "
             "Prêmios e Apostas, Google Trends, ESTBAN)."],
            ["Josué Dantas Martins", "Tratamento estatístico e análise exploratória dos dados: deflacionamento, "
             "tratamento de ausências e de valores atípicos, testes de estacionariedade, decomposição "
             "sazonal e correlação cruzada com defasagens."],
            ["Palmira da Conceição João", "Detecção de quebras estruturais nas séries financeiras nacionais e "
             "construção do indicador composto de exposição territorial (Unidades da Federação e municípios)."],
            ["Pedrina Ferreira Gomes", "Modelagem preditiva comparativa — modelos de referência, modelo "
             "econométrico com variável exógena e modelo de aprendizado de máquina — sob validação temporal "
             "por origem móvel."],
            ["Vinícius Figueiredo Dias Nunes", "Projeção de cenários, simulação do custo de oportunidade "
             "patrimonial e avaliação estatística comparativa dos modelos."],
            ["Wilton da Silva Alves", "Elaboração do painel interativo de consulta aos resultados e "
             "aprofundamento da revisão de literatura."],
            ["Yan Ferreira Martins", "Gestão do cronograma e das entregas, consolidação das referências "
             "bibliográficas, verificação de aderência aos objetivos propostos e redação final da monografia."],
        ],
    )
    legenda(doc, "Quadro 2 — Frente de trabalho principal por integrante do grupo.")

    paragrafo(doc, (
        "O Quadro 3 detalha as atividades planejadas por quinzena, a partir da "
        "Quinzena 3 — as Quinzenas 0 a 2 já foram concluídas com a especificação "
        "do projeto, a definição da metodologia e o envio da Primeira Entrega."
    ), recuo_primeira_linha=1.25)
    tabela_simples(
        doc,
        ["Quinzena", "Período", "Atividades planejadas"],
        [
            ["Quinzena 3", "07/09 a 20/09/2026",
             "Coleta de dados de todas as fontes previstas na metodologia, com verificação de conformidade "
             "com a data de corte estabelecida."],
            ["Quinzena 4", "21/09 a 04/10/2026",
             "Tratamento e análise exploratória da base consolidada; detecção de quebras estruturais e "
             "confronto com o calendário regulatório; início da modelagem preditiva; aprofundamento da "
             "revisão de literatura."],
            ["Quinzena 5", "05/10 a 17/10/2026 — Segunda Entrega",
             "Conclusão da modelagem preditiva comparativa e da avaliação estatística dos modelos; "
             "conclusão do indicador composto territorial; consolidação do relatório da Segunda Entrega."],
            ["Quinzena 6", "18/10 a 01/11/2026",
             "Projeção de cenários e simulação do custo de oportunidade patrimonial; atualização do painel "
             "interativo com os resultados obtidos; verificação de aderência aos objetivos propostos."],
            ["Quinzena 7", "02/11 a 14/11/2026 — Entrega Final",
             "Redação final da monografia, com revisão cruzada por todo o grupo; publicação da base de "
             "dados sob identificador persistente; produção do vídeo de apresentação do trabalho."],
        ],
    )
    legenda(doc, "Quadro 3 — Cronograma de atividades por quinzena.")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SAIDA)
    print(f"Documento gerado em: {SAIDA}")


if __name__ == "__main__":
    main()
