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


def generate_weekly_forecast_pdf(data, narration, map_path, output_path):
    """
    data: structured forecast dictionary
    narration: dict containing GPT-generated sections
    map_path: path to rainfall map image
    output_path: where to save PDF
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
    # SUB COUNTY TABLES
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

        table = Table(table_data, repeatRows=1)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')
        ]))

        elements.append(table)

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
    # APPENDIX (CORRECTED VERSION)
    # =========================

    elements.append(Paragraph("APPENDIX: Interpretation of Terms Used", bold_style))
    elements.append(Spacer(1, 12))


    # ---------------------------------
    # 1. Rainfall Intensity
    # ---------------------------------
    elements.append(Paragraph("1. Rainfall Intensity (24 Hours)", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    rainfall_data = [
        ["Term", "Amount (mm)", "Description"],
        ["Light", "< 5 mm", "Light showers or drizzle"],
        ["Moderate", "5 – 20 mm", "Steady rainfall"],
        ["Heavy", "21 – 50 mm", "Intense rainfall"],
        ["Very Heavy", "> 50 mm", "Very intense rainfall"]
    ]

    rainfall_table = Table(rainfall_data, repeatRows=1)
    rainfall_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))

    elements.append(rainfall_table)
    elements.append(Spacer(1, 18))


    # ---------------------------------
    # 2. Areas Affected
    # ---------------------------------
    elements.append(Paragraph("2. Areas Affected", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    areas_data = [
        ["Coverage Term", "Spatial Coverage"],
        ["Isolated", "Few places (less than 30% of the area)"],
        ["Scattered", "Several places (30% – 60% of the area)"],
        ["Widespread", "Most places (more than 60% of the area)"]
    ]

    areas_table = Table(areas_data, repeatRows=1)
    areas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))

    elements.append(areas_table)
    elements.append(Spacer(1, 18))


    # ---------------------------------
    # 3. Probability of Occurrence
    # ---------------------------------
    elements.append(Paragraph("3. Probability of Occurrence", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    probability_data = [
        ["Probability (%)", "Interpretation"],
        ["0 – 20%", "Low chance"],
        ["21 – 50%", "Moderate chance"],
        ["51 – 80%", "High chance"],
        ["81 – 100%", "Very high chance"]
    ]

    probability_table = Table(probability_data, repeatRows=1)
    probability_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))

    elements.append(probability_table)
    

    # =========================
    # BUILD DOCUMENT
    # =========================

    doc.build(elements)
