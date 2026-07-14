import io
from datetime import date, datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.simulacao import Simulacao
from app.models.servidor import Servidor


def format_currency(val: float) -> str:
    """
    Formata um valor float para o padrão de moeda brasileiro R$ X.XXX,XX.
    """
    if val is None:
        val = 0.0
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(val: float) -> str:
    """
    Formata um valor float para o padrão de percentual brasileiro XX,XX%.
    """
    if val is None:
        val = 0.0
    return f"{val:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def format_date(d: Any) -> str:
    """
    Formata um objeto date/datetime para o padrão brasileiro DD/MM/AAAA.
    """
    if isinstance(d, (date, datetime)):
        return d.strftime("%d/%m/%Y")
    return str(d)


def gerar_pdf_simulacao(simulacao: Simulacao, servidor: Servidor) -> io.BytesIO:
    buffer = io.BytesIO()
    
    # 1. Configurar documento A4 com margens de 36pt (0.5 polegada)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # 2. Configurar estilos
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F2A4A'), # Dark Blue UEFS
        alignment=1, # Centralizado
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1E3D59'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#333333')
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBodyTextCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=body_style,
        fontSize=9,
        leading=12
    )

    table_cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=bold_body_style,
        fontSize=9,
        leading=12
    )

    story = []
    
    # --- Cabeçalho Oficial ---
    story.append(Paragraph("UNIVERSIDADE ESTADUAL DE FEIRA DE SANTANA - UEFS", title_style))
    story.append(Paragraph("Relatório de Simulação de Impacto Financeiro - Evolução de Carreira", subtitle_style))
    story.append(Spacer(1, 10))
    
    # --- Dados do Servidor ---
    item = simulacao.itens[0] if simulacao.itens else None
    vinculo = item.vinculo if item else None
    
    # Tabela de informações do servidor
    info_data = [
        [
            Paragraph("<b>Servidor:</b>", body_style), Paragraph(servidor.nome, body_style),
            Paragraph("<b>CPF:</b>", body_style), Paragraph(servidor.cpf, body_style)
        ],
        [
            Paragraph("<b>Matrícula:</b>", body_style), Paragraph(vinculo.matricula if vinculo else "N/A", body_style),
            Paragraph("<b>Data Admissão:</b>", body_style), Paragraph(format_date(vinculo.data_admissao) if vinculo else "N/A", body_style)
        ],
        [
            Paragraph("<b>Data Vigência Simulação:</b>", body_style), Paragraph(format_date(item.data_vigencia_proposta) if item else "N/A", body_style),
            Paragraph("<b>Mês de Férias:</b>", body_style), Paragraph(str(item.mes_gozo_ferias_proposto) if item else "N/A", body_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[100, 160, 100, 160])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # --- Preparação de dados das tabelas de rubricas ---
    rubricas_chaves = [
        ("salario_base", "Vencimento Base"),
        ("gstu", "GSTU"),
        ("ats", "Adicional por Tempo de Serviço (ATS)"),
        ("cet", "CET"),
        ("insalubridade", "Insalubridade"),
        ("vpess", "VPESS"),
        ("estabilidade", "Estabilidade Econômica"),
    ]
    
    dados_origem = item.dados_origem_json if item else {}
    dados_propostos = item.dados_propostos_json if item else {}
    resultado_calculo = item.resultado_calculo_json if item else {}
    
    # Função auxiliar para gerar dados da tabela de rubricas
    def build_rubric_table_data(dados_json: Dict[str, Any]) -> List[List[Paragraph]]:
        rows = [[Paragraph("Rubrica / Vencimento", table_header_style), Paragraph("Valor (R$)", table_header_style)]]
        for key, label in rubricas_chaves:
            valor = dados_json.get(key, 0.0)
            rows.append([
                Paragraph(label, table_cell_style),
                Paragraph(format_currency(valor), table_cell_style)
            ])
        # Linha do Total
        rows.append([
            Paragraph("Custo Total Mensal", table_cell_bold_style),
            Paragraph(format_currency(dados_json.get("valor_total", 0.0)), table_cell_bold_style)
        ])
        return rows

    # Estilo padrão das tabelas de rubricas
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2A4A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F7F9FB')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EAECEE')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3')),
    ])
    
    # --- Tabela 1: Cenário Atual ---
    story.append(Paragraph("1. Detalhamento do Cenário Atual", section_title_style))
    atual_table_data = build_rubric_table_data(dados_origem)
    atual_table = Table(atual_table_data, colWidths=[380, 140])
    atual_table.setStyle(table_style)
    story.append(atual_table)
    story.append(Spacer(1, 15))
    
    # --- Tabela 2: Cenário Proposto ---
    story.append(Paragraph("2. Detalhamento do Cenário Proposto", section_title_style))
    proposto_table_data = build_rubric_table_data(dados_propostos)
    proposto_table = Table(proposto_table_data, colWidths=[380, 140])
    proposto_table.setStyle(table_style)
    story.append(proposto_table)
    story.append(Spacer(1, 15))
    
    # --- Box de Rodapé com o Impacto Financeiro Consolidado ---
    impacto_bruto = resultado_calculo.get("impacto_financeiro_bruto", 0.0)
    percentual_impacto = resultado_calculo.get("percentual_impacto", 0.0)
    
    summary_data = [
        [
            Paragraph("<b>Diferença Financeira Mensal:</b>", body_style),
            Paragraph(format_currency(impacto_bruto), bold_body_style)
        ],
        [
            Paragraph("<b>Impacto Percentual:</b>", body_style),
            Paragraph(format_percent(percentual_impacto), bold_body_style)
        ],
        [
            Paragraph("<b>Justificativa Requisitos:</b>", body_style),
            Paragraph(item.justificativa_requisitos if item else "", body_style)
        ],
        [
            Paragraph("<b>Data de Geração do Relatório:</b>", body_style),
            Paragraph(format_date(datetime.now().date()), body_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[180, 340])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EDF4FA')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#B0C4DE')),
    ]))
    
    story.append(Paragraph("3. Impacto Financeiro Consolidado", section_title_style))
    story.append(summary_table)
    
    # 3. Construir PDF e fechar
    doc.build(story)
    
    buffer.seek(0)
    return buffer
