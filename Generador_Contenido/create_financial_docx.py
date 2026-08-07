import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_financial_report():
    doc = Document()

    # Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Executive Palette
    COLOR_PRIMARY = RGBColor(0x0F, 0x2A, 0x4A)    # Corporate Navy
    COLOR_SECONDARY = RGBColor(0x1B, 0x6B, 0x93)  # Steel Blue
    COLOR_DARK = RGBColor(0x22, 0x22, 0x22)       # Text dark
    COLOR_MUTED = RGBColor(0x55, 0x55, 0x55)      # Subdued gray

    HEX_PRIMARY = "0F2A4A"
    HEX_SECONDARY = "1B6B93"
    HEX_LIGHT_BG = "F2F5F8"
    HEX_ALT_ROW = "F7FAFC"
    HEX_HIGHLIGHT = "E8F4F8"

    def add_title(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(16)
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(12)
        run.font.italic = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_p(text, bold_prefix="", space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(11)
            r_pre.font.bold = True
            r_pre.font.color.rgb = COLOR_DARK
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.color.rgb = COLOR_DARK
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(11)
            r_pre.font.bold = True
            r_pre.font.color.rgb = COLOR_DARK
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.color.rgb = COLOR_DARK
        return p

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    def make_callout(text, title="DICTAMEN DE ASIGNACIÓN PRESUPUESTARIA"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, HEX_HIGHLIGHT)
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="single" w:sz="36" w:space="0" w:color="{HEX_PRIMARY}"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
        tcPr.append(borders)
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run_title = p.add_run(f"💰 {title}\n")
        run_title.font.name = "Arial"
        run_title.font.bold = True
        run_title.font.color.rgb = COLOR_PRIMARY
        run_title.font.size = Pt(10.5)
        run_text = p.add_run(text)
        run_text.font.name = "Calibri"
        run_text.font.size = Pt(10.5)
        run_text.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # HEADER & METADATA
    add_title("INFORME DE PLANIFICACIÓN FINANCIERA Y PRESUPUESTARIA UEI")
    add_subtitle("Análisis Ejecutivo de Costos Directos, Margen de Contingencia y Asignación de Presupuesto para Sistema Híbrido (90 Docentes)")

    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(12)
    meta_run = meta_p.add_run("Destinatario: Dirección Financiera / Coordinación General | Basado en Tarifas Directas Oficiales Google & DeepSeek | Agosto 2026")
    meta_run.font.name = "Calibri"
    meta_run.font.size = Pt(9.5)
    meta_run.font.color.rgb = COLOR_MUTED

    make_callout(
        "Se recomienda la asignación de un PRESUPUESTO MENSUAL TOTAL DE $11.73 USD ($117.30 USD por año lectivo de 10 meses) para atender la demanda operativa de los 90 docentes institucionales. Este monto incluye un Costo Operacional Base de $7.33 USD/mes más un Fondo de Reserva y Contingencia de $4.40 USD/mes (+60%) destinado a cubrir picos de demanda en períodos de exámenes, reintentos de generación y sobrecarga de volumen.",
        "CIFRA FINAL RECOMENDADA PARA ASIGNACIÓN DE PRESUPUESTO"
    )

    # SECCIÓN 1: INTRODUCCIÓN FINANCIERA
    add_h1("1. Propósito del Análisis Financiero")
    add_p("El objetivo del presente informe es establecer la partida presupuestaria necesaria para respaldar el consumo de Inteligencia Artificial del aplicativo UEI bajo una infraestructura Híbrida de alta eficiencia. El análisis excluye terminología técnica de desarrollo y se enfoca exclusivamente en variables financieras, volumen de uso docente, tarifas oficiales de proveedores y gestión de riesgos presupuestarios.")

    # SECCIÓN 2: TARIFAS OFICIALES
    add_h1("2. Tarifas Directas de Proveedores Oficiales")
    add_p("Los cálculos presentados en este documento se sustentan estrictamente en las tarifas de facturación publicadas en los portales oficiales de Google Cloud (Gemini API) y DeepSeek Official API:")

    tbl_rates = doc.add_table(rows=3, cols=4)
    tbl_rates.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_r = ["Proveedor Oficial", "Modelo Asignado", "Tarifa Token Entrada (Input) / 1M", "Tarifa Token Salida (Output) / 1M"]
    data_r = [
        ["Google Cloud (Gemini API)", "Gemini 2.5 Flash", "$0.075 USD", "$0.300 USD"],
        ["DeepSeek Official API", "DeepSeek-V3 / Flash", "$0.140 USD", "$0.280 USD"],
    ]
    for col_idx, h in enumerate(headers_r):
        cell = tbl_rates.cell(0, col_idx)
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for row_idx, row_data in enumerate(data_r, start=1):
        bg = HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row_data):
            cell = tbl_rates.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # SECCIÓN 3: ESTRUCTURA DE COSTOS POR PILAR DEL SISTEMA
    add_h1("3. Estructura de Costos por Pilar Operativo del Sistema")
    add_p("El sistema está compuesto por 3 módulos de trabajo diferenciados según el servicio educativo prestado:")

    add_h2("Pilar 1: El Validador (Concordancia Curricular)")
    add_p("Analiza los sílabos semanales frente a las guías didácticas y dictamina el cumplimiento de los aprendizajes institucionales. Procesado con DeepSeek Official API.")
    add_bullet("Costo Unitario Base por Validación: $0.000882 USD (menos de 1 décimo de centavo).")

    add_h2("Pilar 2: El Generador (Digitalización de PDFs y Páginas Escaneadas)")
    add_p("Procesa folletos, libros y documentos en PDF (incluyendo escaneos de pura imagen sin texto reconocible) y los convierte a formato estructurado interactivo. Procesado con Google Gemini API.")
    add_bullet("Costo Unitario Base por Página Escaneada OCR a HTML: $0.000615 USD.")

    add_h2("Pilar 3: El Módulo de Lúdicas (Juegos y Actividades Didácticas)")
    add_p("Genera la suite de 7 recursos pedagógicos lúdicos (crucigramas, sopas de letras, tarjetas 3D, rompecabezas de lógica, cuestionarios, diagramas y guías de estudio). Procesado con DeepSeek Official API.")
    add_bullet("Costo Unitario Base por Recurso Lúdico Generado: $0.000518 USD.")

    # SECCIÓN 4: MODELO DE CARGA Y PRESUPUESTO BASE
    add_h1("4. Modelo de Consumo Mensual Base (90 Docentes)")
    add_p("Tomando como referencia el perfil de demanda alta de la institución (90 docentes activos con un promedio mensual de 100 páginas escaneadas, 30 actividades lúdicas y 5 validaciones curriculares por docente):")

    tbl_base = doc.add_table(rows=5, cols=5)
    tbl_base.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_b = ["Pilar Operativo", "Proveedor Oficial", "Volumen Mensual (90 Docentes)", "Costo Unitario", "Costo Mensual Base"]
    data_b = [
        ["1. El Validador", "DeepSeek Official", "450 validaciones / mes", "$0.000882 USD", "$0.397 USD"],
        ["2. El Generador (PDF Escaneados)", "Google Gemini API", "9,000 páginas / mes", "$0.000615 USD", "$5.535 USD"],
        ["3. El de Lúdicas (MCP)", "DeepSeek Official", "2,700 recursos / mes", "$0.000518 USD", "$1.399 USD"],
        ["TOTAL OPERACIONAL NETO BASE", "Sistema Híbrido", "12,150 operaciones / mes", "-", "$7.331 USD / mes"],
    ]
    for col_idx, h in enumerate(headers_b):
        cell = tbl_base.cell(0, col_idx)
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(9.0)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for row_idx, row_data in enumerate(data_b, start=1):
        bg = HEX_HIGHLIGHT if row_idx == 4 else (HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF")
        for col_idx, val in enumerate(row_data):
            cell = tbl_base.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=90, bottom=90, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 1 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.0)
            if row_idx == 4 or col_idx == 4:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # SECCIÓN 5: MARGEN DE CONTINGENCIA Y FONDO DE RESERVA
    add_h1("5. Análisis de Riesgo y Reserva de Contingencia (+60%)")
    add_p("Para garantizar que la institución nunca experimente interrupciones por agotamiento de saldo en las cuentas de API, se establece un Margen de Reserva y Contingencia Financiera del +60% fundamentado en 3 factores de riesgo operativo:")
    
    add_bullet(" Períodos de cierres quimestrales y exámenes finales donde los docentes duplican la producción de materiales.", "A. Picos de Demanda Quimestral (+30%):")
    add_bullet(" Solicitudes de regeneración por parte del profesorado al ajustar parámetros didácticos.", "B. Reintentos y Ajustes del Docente (+15%):")
    add_bullet(" Transcripción de documentos escaneados con calidad compleja o longitud extendida.", "C. Variabilidad de Extensión en Contenidos (+15%):")

    add_p("La suma de la operación base ($7.33 USD) más el fondo de contingencia ($4.40 USD) constituye el monto definitivo sugerido para aprobación presupuestaria.", space_after=8)

    # SECCIÓN 6: PROYECCIÓN Y DESTINACIÓN DE PRESUPUESTO
    add_h1("6. Proyección Temporal para Asignación de Presupuesto Institucional")
    add_p("A continuación se presenta la tabla de asignación presupuestaria final recomendada para su aprobación por parte de la Dirección Financiera:")

    tbl_proj = doc.add_table(rows=4, cols=4)
    tbl_proj.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_p = ["Período de Asignación", "Costo Operacional Base", "Reserva de Contingencia (+60%)", "PRESUPUESTO TOTAL RECOMENDADO"]
    data_p = [
        ["Presupuesto Mensual", "$7.33 USD", "$4.40 USD", "$11.73 USD / mes"],
        ["Presupuesto Trimestral", "$21.99 USD", "$13.20 USD", "$35.19 USD / trimestre"],
        ["Presupuesto Anual Lectivo (10 Meses)", "$73.30 USD", "$44.00 USD", "$117.30 USD / año lectivo"],
    ]
    for col_idx, h in enumerate(headers_p):
        cell = tbl_proj.cell(0, col_idx)
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for row_idx, row_data in enumerate(data_p, start=1):
        bg = HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row_data):
            cell = tbl_proj.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if col_idx == 3:
                r.font.bold = True
                r.font.color.rgb = COLOR_SECONDARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # SECCIÓN 7: COMPARATIVA DE RETORNO Y AHORRO
    add_h1("7. Retorno de Inversión y Comparativa de Ahorro Institucional")
    add_p("Frente al modelo actual basado en Claude Sonnet (cuyo costo anual asciende a $4,800.00 USD para esta misma carga), la implementación del Sistema Híbrido permite un ahorro económico directo del 97.6%:")
    
    add_bullet("Gasto Anual Proyectado con Claude Sonnet: ~$4,800.00 USD / año lectivo.", "")
    add_bullet("Presupuesto Anual Sistema Híbrido (Con 60% Contingencia Incluido): $117.30 USD / año lectivo.", "")
    add_bullet("AHORRO FINANCIERO NETO ANUAL PARA LA INSTITUCIÓN: $4,682.70 USD / año.", "")

    make_callout(
        "Aprobar la asignación mensual de $11.73 USD garantiza la sostenibilidad financiera absoluta del aplicativo UEI para los 90 docentes, protegiendo a la institución ante cualquier sobrecarga de uso y logrando una eficiencia presupuestaria del 97.6%.",
        "CONCLUSIÓN DE GESTIÓN PRESUPUESTARIA"
    )

    try:
        doc.save("c:\\Users\\User\\Desktop\\Proyecto Validador UEI\\Unidad-Educativa\\Informe_Financiero_Presupuestario_UEI.docx")
        print("Informe guardado en c:\\Users\\User\\Desktop\\Proyecto Validador UEI\\Unidad-Educativa\\Informe_Financiero_Presupuestario_UEI.docx")
    except PermissionError:
        doc.save("c:\\Users\\User\\Desktop\\Proyecto Validador UEI\\Unidad-Educativa\\Informe_Financiero_Presupuestario_UEI_v2.docx")
        print("Informe guardado en c:\\Users\\User\\Desktop\\Proyecto Validador UEI\\Unidad-Educativa\\Informe_Financiero_Presupuestario_UEI_v2.docx")

if __name__ == "__main__":
    create_financial_report()
