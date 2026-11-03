from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HEADERS = ["Roll No", "Name", "Email", "Phone", "Department", "Class",
           "Marks", "Attendance %", "Fees"]


def _row(s):
    return [s.roll_number, s.full_name, s.email, s.phone, s.department, s.class_name,
            f"{float(s.marks):.2f}", f"{float(s.attendance):.2f}",
            "Paid" if s.fees_paid else "Pending"]


def build_xlsx(students):
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for s in students:
        ws.append(_row(s))
    for row in ws.iter_rows(min_row=2):          # keep text like "=1+1" as text
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith(("=", "+", "-", "@")):
                cell.data_type = "s"
    for col in ws.columns:
        longest = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(longest + 2, 10), 40)
    ws.freeze_panes = "A2"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_docx(students):
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    doc.add_heading("Student Report", level=1)
    doc.add_paragraph(f"Generated: {datetime.now():%d %b %Y, %H:%M}")
    table = doc.add_table(rows=1, cols=len(HEADERS))
    table.style = "Table Grid"
    for i, name in enumerate(HEADERS):
        run = table.rows[0].cells[i].paragraphs[0].add_run(name)
        run.bold = True
        run.font.size = Pt(9)
    for s in students:
        cells = table.add_row().cells
        for i, value in enumerate(_row(s)):
            cells[i].paragraphs[0].add_run(str(value)).font.size = Pt(9)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_pdf(students):
    buf = BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                            topMargin=24, bottomMargin=24, title="Student Report")
    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"]
    cell_style.fontSize = 8
    cell_style.leading = 10
    data = [HEADERS] + [[Paragraph(escape(str(v)), cell_style) for v in _row(s)]
                        for s in students]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f9")]),
    ]))
    pdf.build([
        Paragraph("Student Report", styles["Title"]),
        Paragraph(f"Generated: {datetime.now():%d %b %Y, %H:%M} | Records: {len(students)}",
                  styles["Normal"]),
        Spacer(1, 10), table,
    ])
    return buf.getvalue()