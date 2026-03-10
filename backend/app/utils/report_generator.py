from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import ListFlowable, ListItem


def generate_weekly_forecast_pdf(data, narration, map_path, output_path, signoff=None):
    """
    data: structured forecast dictionary
    narration: dict containing GPT-generated sections
    map_path: path to rainfall map image
    output_path: where to save PDF
    signoff: dict containing dynamic user sign-off details
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=pagesizes.A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []

    styles = getSampleStyleSheet()

    # Custom styles
    centered_style = ParagraphStyle(
        name='CenteredTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=10
    )

    normal_style = styles['Normal']
    bold_style = styles['Heading2']

    # =========================
    # COVER PAGE
    # =========================

    elements.append(Paragraph("REPUBLIC OF KENYA", centered_style))
    elements.append(Paragraph("MINISTRY OF ENVIRONMENT CLIMATE CHANGE AND FORESTRY", centered_style))
    elements.append(Paragraph("KENYA METEOROLOGICAL DEPARTMENT", centered_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"{data['meta']['station']}", styles['Heading3']))
    elements.append(Paragraph(f"{data['meta']['county']}", styles['Heading3']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("WEEKLY WEATHER FORECAST", centered_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Date of issue:</b> {data['meta']['issue_date']}", normal_style))
    elements.append(Paragraph(f"<b>Period of forecast:</b> {data['meta']['period']}", normal_style))
    elements.append(Spacer(1, 20))

    # Insert map
    if map_path:
        img = Image(map_path, width=4.5 * inch, height=6 * inch)
        img.hAlign = 'CENTER'
        elements.append(img)

    elements.append(PageBreak())

    # =========================
    # PART I – WEEKLY SUMMARY
    # =========================

    elements.append(Paragraph("PART I: Weekly Weather Forecast Summary", bold_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(narration["weekly_summary_text"], normal_style))
    elements.append(Spacer(1, 12))

    # =========================
    # SUB COUNTY TABLES - CHANGED SECTION
    # =========================

    for sub in data["sub_counties"]:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(sub["title"], styles["Heading3"]))
        elements.append(Spacer(1, 8))

        table_data = []

        # Header row
        header_row = [""] + sub["days"]
        table_data.append(header_row)

        # Add rows dynamically
        rows = [
            "Morning",
            "Afternoon",
            "Night",
            "Rainfall distribution",
            "Maximum temperature",
            "Minimum temperature",
            "Winds"
        ]

        for row_name in rows:
            row = [row_name]
            for day in sub["days"]:
                row.append(sub["forecast"][day][row_name])
            table_data.append(row)

        # Calculate column widths for better horizontal appearance
        num_cols = len(sub["days"]) + 1
        page_width = doc.width
        # First column (row name) gets 25% width, remaining 75% split evenly among days
        col_widths = [page_width * 0.25] + [page_width * 0.75 / (num_cols - 1)] * (num_cols - 1)
        
        table = Table(table_data, repeatRows=1, colWidths=col_widths)

        table.setStyle(TableStyle([
            # Header row styling (light gray)
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            # First column styling (light gray)
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            # All other cells (light green)
            ('BACKGROUND', (1, 1), (-1, -1), colors.lightgreen),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical center for all cells
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),    # Horizontal center for all cells
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        # Add extra vertical space after table
        elements.append(Spacer(1, 24))  # Increased from default to 24 points

        elements.append(PageBreak())

    # =========================
    # PART II – MARINE WEATHER
    # =========================

    elements.append(Paragraph("PART II: 7 Days Marine Weather", bold_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(narration["marine_summary_text"], normal_style))
    elements.append(Spacer(1, 12))

    marine_table_data = [
        ["Day", "Max Wind (Knots)"]
    ]

    for day, wind in data["marine"]["daily_wind"].items():
        marine_table_data.append([day, wind])

    marine_table = Table(marine_table_data, repeatRows=1)

    marine_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))

    elements.append(marine_table)
    elements.append(PageBreak())

    # =========================
    # APPENDIX
    # =========================
    elements.append(Paragraph("APPENDIX 1: INTERPRETATION OF TERMS USED.", bold_style))
    elements.append(Spacer(1, 10))

    appendix_table_width = doc.width * 0.85

    def build_appendix_table(table_data, col_ratios):
        col_widths = [appendix_table_width * ratio for ratio in col_ratios]
        table = Table(table_data, repeatRows=1, colWidths=col_widths, hAlign="LEFT")
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return table

    # (a) Rainfall terms
    elements.append(Paragraph("(a)", normal_style))
    elements.append(Spacer(1, 4))
    rainfall_data = [
        ["Term", "Rainfall Amount [24hrs]", "Description"],
        ["Light", "< 5mm", "Gentle rain, drizzle."],
        ["Moderate", "5 - 20 mm", "Steady, noticeable rain."],
        ["Heavy", "21 - 50 mm", "Intense rain, possible thunder."],
        ["Very Heavy", ">50 mm", "Prolonged rain."],
    ]
    elements.append(build_appendix_table(rainfall_data, [0.22, 0.28, 0.50]))
    elements.append(Spacer(1, 12))

    # (b) Area affected terms
    elements.append(Paragraph("(b)", normal_style))
    elements.append(Spacer(1, 4))
    areas_data = [
        ["Term", "Area Affected", "Description"],
        ["Few places", "<33%", "Rain in a small portion of the region."],
        ["Several places", "33% to 66%", "Rain in multiple but not most parts of the region."],
        ["Most places", ">66%", "Rain in nearly all parts of the region."],
    ]
    elements.append(build_appendix_table(areas_data, [0.22, 0.23, 0.55]))
    elements.append(Spacer(1, 12))

    # (c) Probability terms
    elements.append(Paragraph("(c)", normal_style))
    elements.append(Spacer(1, 4))
    probability_data = [
        ["Term.", "Probability of Occurrence", "Description."],
        ["Possible", "10 - 30 %", "There is low confidence."],
        ["Chance of/ May", "31 - 50 %", "There is moderate confidence."],
        ["Likely", "51 - 75 %", "The event is more probable than not."],
        ["Expected", "76 - 90 %", "There is high confidence."],
        ["Very Likely", "91 - 99 %", "There is very high confidence. Almost certain."],
        ["Certain", "100 %", "The event is guaranteed to occur."],
    ]
    elements.append(build_appendix_table(probability_data, [0.22, 0.28, 0.50]))
    elements.append(PageBreak())

    # =========================
    # ACKNOWLEDGEMENT + SIGN-OFF
    # =========================
    signoff = signoff or {}
    signoff_name = signoff.get("name") or "N/A"
    signoff_title = signoff.get("job_title") or "N/A"
    signoff_mobile = signoff.get("mobile") or "N/A"
    signoff_email = signoff.get("email") or "N/A"

    elements.append(Paragraph(
        "In concurrence with outputs from relevant marine data platforms, acknowledgment is fully accorded to:",
        normal_style
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "ESSO- Indian National Centre for Ocean Information Services (INCOIS), Mercator-ocean.fr, COPERNICUS",
        normal_style
    ))
    elements.append(Paragraph(
        "Marine Environment Monitoring Service (CMEMS) and other related sources.",
        normal_style
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"{signoff_name}.", normal_style))
    elements.append(Paragraph(signoff_title, normal_style))
    elements.append(Paragraph(f"Mobile: {signoff_mobile}", normal_style))
    elements.append(Paragraph(f"Email {signoff_email}", normal_style))

    # =========================
    # BUILD DOCUMENT
    # =========================

    doc.build(elements)
