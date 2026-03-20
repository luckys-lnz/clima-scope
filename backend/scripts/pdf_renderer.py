import csv
import os
import re
import string
from pathlib import Path
from typing import Optional

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
WEATHER_CODE_ICON_MAP = {
    0: "clear-day",
    1: "partly-cloudy-day",
    2: "partly-cloudy-day",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    80: "rain",
    81: "rain",
    82: "thunderstorm",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}

DEGREE_SYMBOL = "°C"


def _resolve_weather_icon_path(icon_name: str) -> Optional[str]:
    candidates = [
        _resolve_asset_path(f"assets/weather_icons/{icon_name}.png"),
        _resolve_asset_path(f"assets/weather-icons/{icon_name}.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _icon_name_from_description(text: str) -> str:
    lowered = str(text or "").lower()
    if any(word in lowered for word in ["thunder", "storm"]):
        return "thunderstorm"
    if any(word in lowered for word in ["showers", "rain"]):
        return "rain"
    if "drizzle" in lowered:
        return "drizzle"
    if any(word in lowered for word in ["mist", "fog"]):
        return "fog"
    if any(word in lowered for word in ["sun", "clear"]):
        return "clear-day"
    if "partly" in lowered:
        return "partly-cloudy-day"
    if "cloud" in lowered:
        return "cloudy"
    return "mostly-cloudy"


def _icon_path_for_weather_code(code: Optional[float]) -> Optional[str]:
    icon_name = None
    if code is not None:
        try:
            code_int = int(code)
            icon_name = WEATHER_CODE_ICON_MAP.get(code_int)
        except (TypeError, ValueError):
            icon_name = None
    if not icon_name:
        return None
    return _resolve_weather_icon_path(icon_name)


def _sanitize_text(text: str) -> str:
    if not text:
        return ""
    # Keep printable ASCII and common Unicode letters, digits, punctuation, and spaces
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + " °C°–→"  # keep °, dash, arrow
    return "".join(c for c in text if c in allowed_chars or c.isalpha() or c.isspace())


def _resolve_asset_path(relative_path: str) -> str:
    base_dir = Path(__file__).resolve().parent
    return str(base_dir / relative_path)


def _scale_image_to_fit(img: Image, max_width: float, max_height: float) -> Image:
    img._restrictSize(max_width, max_height)
    return img


def _format_temperature_value(text: str) -> str:
    if not text:
        return text
    cleaned = _sanitize_text(text).strip()
    if not cleaned:
        return cleaned
    if "°" in cleaned or "C" in cleaned:
        cleaned = re.sub(r"\s*°\s*C", "°C", cleaned)
        cleaned = re.sub(r"°C\s*°C", "°C", cleaned)
        return cleaned
    if re.search(r"\d", cleaned):
        return f"{cleaned}{DEGREE_SYMBOL}"
    return cleaned


def _extract_wind_range(value: str) -> str:
    if not value:
        return value
    numbers = re.findall(r"\d+(?:\.\d+)?", value)
    if not numbers:
        return value.strip()
    if len(numbers) == 1:
        return numbers[0]
    return f"{numbers[0]} - {numbers[-1]}"


def _build_weather_cell(
    text: str,
    weather_code: Optional[float],
    text_style: ParagraphStyle,
):
    icon_path = _icon_path_for_weather_code(weather_code)
    if not icon_path:
        icon_path = _resolve_weather_icon_path(_icon_name_from_description(text))
    if not icon_path:
        return Paragraph(text, text_style)

    icon_size = 14.0
    icon_img = Image(icon_path, width=icon_size, height=icon_size)
    icon_img.hAlign = "CENTER"
    icon_table = Table(
        [[icon_img], [Paragraph(text, text_style)]],
        colWidths=[None],
    )
    icon_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return icon_table


def _wind_range_color(value: str):
    if not value:
        return None
    numbers = re.findall(r"\d+(?:\.\d+)?", value)
    if not numbers:
        return None
    max_value = max(float(n) for n in numbers)
    if max_value <= 7:
        return colors.green
    if max_value <= 21:
        return colors.yellow
    return colors.red


def _build_wind_badge(value: str, base_style: ParagraphStyle):
    color = _wind_range_color(value)
    if not color:
        return Paragraph(value, base_style)
    hex_color = f"#{color.hexval()}"
    return Paragraph(
        f'<font backcolor="{hex_color}">&nbsp;{value}&nbsp;</font>',
        base_style,
    )


def generate_marine_csv(api_data, output_file: str) -> None:
    daily_wind = {}
    if isinstance(api_data, dict):
        if isinstance(api_data.get("daily_wind"), dict):
            daily_wind = api_data["daily_wind"]
        elif isinstance(api_data.get("daily"), dict):
            daily = api_data["daily"]
            times = daily.get("time") or daily.get("dates") or []
            winds = daily.get("wind_speed_10m_max") or daily.get("winds") or []
            if len(times) == len(winds):
                daily_wind = {str(day): str(wind) for day, wind in zip(times, winds)}

    with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Day", "Wind Range"])
        for day, wind in daily_wind.items():
            writer.writerow([day, _extract_wind_range(str(wind))])


def _read_marine_csv(csv_path: str) -> tuple[list[str], list[str]]:
    days = []
    winds = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            days.append(row.get("Day", "").strip())
            winds.append(_extract_wind_range(row.get("Wind Range", "").strip()))
    return days, winds


def _extract_numeric_values(text: str) -> list[float]:
    if not text:
        return []
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]


def _format_range(values: list[float]) -> Optional[str]:
    if not values:
        return None
    return f"{min(values):.0f}–{max(values):.0f}"


def _summarize_morning_conditions(rows: list[dict]) -> str:
    if not rows:
        return "cloudy mornings with sunny intervals"
    bucket = {"sunny": 0, "cloudy": 0, "rain": 0}
    for row in rows:
        text = str(row or "").lower()
        if any(word in text for word in ["rain", "showers", "drizzle", "storm"]):
            bucket["rain"] += 1
        elif any(word in text for word in ["cloud", "overcast"]):
            bucket["cloudy"] += 1
        elif any(word in text for word in ["sun", "clear"]):
            bucket["sunny"] += 1
    if bucket["rain"] >= max(bucket["cloudy"], bucket["sunny"]):
        return "cloudy mornings with light showers"
    if bucket["cloudy"] >= bucket["sunny"]:
        return "cloudy mornings with sunny intervals"
    return "mostly sunny mornings"


def _format_weekly_summary(text: str, data: dict) -> str:
    sub_counties = data.get("sub_counties") or []
    if not sub_counties:
        return text or ""

    max_values = []
    min_values = []
    wind_values = []
    morning_values = []
    for sub in sub_counties:
        forecast = sub.get("forecast") or {}
        for _, day_rows in forecast.items():
            max_values += _extract_numeric_values(day_rows.get("Maximum temperature", ""))
            min_values += _extract_numeric_values(day_rows.get("Minimum temperature", ""))
            wind_values += _extract_numeric_values(day_rows.get("Winds", ""))
            morning_values.append(day_rows.get("Morning", ""))

    max_range = _format_range(max_values) or "30–34"
    min_range = _format_range(min_values) or "21–25"
    wind_range = _format_range(wind_values) or "10–25"
    morning_phrase = _summarize_morning_conditions(morning_values)

    template = (
        f"→ The county will generally experience {morning_phrase} through the week, "
        "with mostly dry conditions across all sub-counties. Light showers may occur in a few places.<br/><br/>"
        f"→ Maximum/Daytime temperatures are expected to range from {max_range}°C.<br/><br/>"
        f"→ Minimum/Night temperatures are expected to range from {min_range}°C.<br/><br/>"
        f"→ Moderate to strong Northeasterly (NE) to East-Northeasterly (ENE) winds ({wind_range} knots) are expected "
        "throughout the week.<br/><br/>"
        "→ Marine users are strongly advised to exercise caution the rest of the week.<br/><br/>"
        "→ Any significant change in the forecast will be shared in your WhatsApp groups."
    )
    sanitized = _sanitize_text(template)
    return sanitized


def _aggregate_marine_wind_from_subcounties(data: dict) -> Optional[dict]:
    sub_counties = data.get("sub_counties") or []
    if not sub_counties:
        return None

    day_labels = sub_counties[0].get("days") or []
    if not day_labels:
        return None

    aggregated = {}
    for day in day_labels:
        day_values = []
        for sub in sub_counties:
            day_rows = (sub.get("forecast") or {}).get(day, {})
            day_values += _extract_numeric_values(day_rows.get("Winds", ""))
        if day_values:
            aggregated[day] = f"{min(day_values):.0f} - {max(day_values):.0f}"
    return aggregated or None


def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(200 * mm, 15, text)


def generate_weekly_forecast_pdf(data, narration, map_path, output_path, signoff=None):

    doc = SimpleDocTemplate(
        output_path,
        pagesize=pagesizes.A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40
    )

    elements = []

    styles = getSampleStyleSheet()

    cover_header_style = ParagraphStyle(
        name="CoverHeader",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        spaceAfter=2,
    )
    cover_middle_style = ParagraphStyle(
        name="CoverMiddle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        spaceAfter=3,
    )
    cover_date_style = ParagraphStyle(
        name="CoverDate",
        parent=styles["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        spaceAfter=2,
    )

    section_style = ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        spaceAfter=10,
        spaceBefore=10
    )

    normal_style = styles["Normal"]
    bold_style = section_style
    summary_style = ParagraphStyle(
        name="WeeklySummary",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        spaceAfter=6,
        leftIndent=16,
    )

    subcounty_title_style = ParagraphStyle(
        name="SubCountyTitle",
        parent=styles["Heading4"],
        fontSize=11,
        leading=13,
        spaceAfter=4,
    )

    # =========================
    # COVER PAGE
    # =========================

    coat_path = _resolve_asset_path("assets/coat_of_arms.png")
    if os.path.exists(coat_path):
        coat_img = Image(coat_path, width=80, height=80)
        coat_img.hAlign = "CENTER"
        elements.append(coat_img)
        elements.append(Spacer(1, 8))

    elements.append(Paragraph("REPUBLIC OF KENYA", cover_header_style))
    elements.append(Paragraph("MINISTRY OF ENVIRONMENT CLIMATE CHANGE AND FORESTRY", cover_header_style))
    elements.append(Paragraph("KENYA METEOROLOGICAL DEPARTMENT", cover_header_style))
    elements.append(Spacer(1, 14))

    profile = data.get("profile") or {}
    station_name = _sanitize_text(
        profile.get("station_name")
        or data["meta"].get("station_name")
        or profile.get("station")
        or data["meta"].get("station")
        or ""
    )
    station_address = _sanitize_text(
        profile.get("station_address")
        or data["meta"].get("station_address")
        or ""
    )
    county_name = _sanitize_text(
        profile.get("county")
        or data["meta"].get("county")
        or ""
    )
    if station_name:
        elements.append(Paragraph(station_name, cover_middle_style))
    if station_address:
        elements.append(Paragraph(station_address, cover_middle_style))
    if county_name:
        elements.append(Paragraph(f"{county_name.upper()} COUNTY", cover_middle_style))

    elements.append(Paragraph("WEEKLY WEATHER FORECAST", cover_middle_style))
    elements.append(Spacer(1, 10))

    period_start = _sanitize_text(data["meta"].get("period_start") or "")
    period_end = _sanitize_text(data["meta"].get("period_end") or "")
    if (not period_start or not period_end) and data["meta"].get("period"):
        period_text = str(data["meta"]["period"])
        if " to " in period_text:
            maybe_start, maybe_end = period_text.split(" to ", 1)
            period_start = period_start or _sanitize_text(maybe_start)
            period_end = period_end or _sanitize_text(maybe_end)

    elements.append(Paragraph(f"Date of issue: {_sanitize_text(data['meta'].get('issue_date', ''))}", cover_date_style))
    elements.append(Paragraph(f"Period of forecast: {period_start} to {period_end}", cover_date_style))
    elements.append(Spacer(1, 6))

    if map_path:
        map_img = Image(map_path)
        # Fill remaining cover-page space as much as possible after the header sections.
        map_img = _scale_image_to_fit(map_img, doc.width, doc.height * 0.62)
        map_img.hAlign = "CENTER"
        elements.append(map_img)

    elements.append(PageBreak())

    # =========================
    # PART I – WEEKLY SUMMARY
    # =========================

    elements.append(Paragraph("PART I: Weekly Weather Forecast Summary", bold_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(_format_weekly_summary(narration.get("weekly_summary_text", ""), data), summary_style))
    elements.append(Spacer(1, 12))

    # =========================
    # SUB COUNTY TABLES
    # =========================

    cell_style = ParagraphStyle(
        name="CellStyle",
        fontSize=8,
        leading=10,
        alignment=1,
        wordWrap="CJK",
    )
    row_header_style = ParagraphStyle(
        name="RowHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=1,
        wordWrap="CJK",
    )

    marine_badge_style = ParagraphStyle(
        name="MarineBadgeStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=1,
    )

    for sub in data["sub_counties"]:
        table_data = []

        header_row = [""] + sub["days"]
        table_data.append(header_row)

        rows = [
            "Morning",
            "Afternoon",
            "Night",
            "Rainfall distribution",
            "Maximum temperature",
            "Minimum temperature",
            "Winds"
        ]
        weather_rows = {"Morning", "Afternoon", "Night"}

        for row_name in rows:

            row = [Paragraph(row_name, row_header_style)]

            for day in sub["days"]:
                cell_text = _sanitize_text(sub["forecast"].get(day, {}).get(row_name, ""))
                if row_name in {"Maximum temperature", "Minimum temperature"}:
                    cell_text = _format_temperature_value(cell_text)
                if row_name in weather_rows:
                    weather_code = sub["forecast"].get(day, {}).get("_weather_code")
                    row.append(_build_weather_cell(cell_text, weather_code, cell_style))
                else:
                    row.append(Paragraph(cell_text, cell_style))

            table_data.append(row)
        
        # Get full page A4
        full_page_width = A4[0]

        available_width = full_page_width * 0.96

        num_cols = len(sub["days"]) + 1
        first_col_width = available_width * 0.15
        day_col_width = available_width * 0.85 / (num_cols - 1)

        col_widths = [first_col_width] + [day_col_width] * (num_cols - 1)

        table = Table(table_data, repeatRows=1, colWidths=col_widths, splitByRow=0)
        table.keepWithNext = True

        # Calculate position to center on Full A4 page
        left_position = (full_page_width - available_width) / 2

        # Manually position the table
        table._hAlign = 'LEFT'
        table._left = left_position

        table.setStyle(TableStyle([

            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#eeeeee')),
            ('BACKGROUND', (1, 1), (-1, -1), colors.HexColor('#eaf3e5')),

            # Outer border (sharp box around entire table)
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            
            # Inner grid lines (single thickness, no overlap)
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),

            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),

            ('FONTSIZE', (0, 0), (-1, 0), 9),

            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        part_i_table_block = [
            Spacer(1, 20),
            Paragraph(sub["title"], subcounty_title_style),
            Spacer(1, 8),
            table,
        ]
        elements.append(KeepTogether(part_i_table_block))
        elements.append(Spacer(1, 30))
        elements.append(PageBreak())

    # =========================
    # PART II – MARINE WEATHER
    # =========================

    elements.append(Paragraph("PART II: 7 Days Marine Weather", bold_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(_sanitize_text(narration["marine_summary_text"]), normal_style))
    elements.append(Spacer(1, 12))


    # =========================
    # Table I
    # =========================

    elements.append(Paragraph(
        "Table I: Ocean wave height and wind speed for Kenyan waters.",
        subcounty_title_style
    ))
    elements.append(Spacer(1, 10))


    marine_csv_path = os.path.join(os.path.dirname(output_path), "marine_wind.csv")
    marine_aggregate = _aggregate_marine_wind_from_subcounties(data)
    marine_payload = {"daily_wind": marine_aggregate} if marine_aggregate else data.get("marine", {})
    generate_marine_csv(marine_payload, marine_csv_path)
    days, winds = _read_marine_csv(marine_csv_path)

    if not days or not winds:
        source = marine_aggregate or data.get("marine", {}).get("daily_wind", {})
        days = list(source.keys())
        winds = [_extract_wind_range(str(v)) for v in source.values()]

    marine_table_data = [
        ["DAYS"] + days,
        [Paragraph("MAX<br/>Wind<br/>In knots.", normal_style)]
        + [_build_wind_badge(str(wind), marine_badge_style) for wind in winds]
    ]

    marine_table = Table(
        marine_table_data,
        repeatRows=1,
        colWidths=[doc.width / (len(days) + 1)] * (len(days) + 1)
    )

    marine_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(marine_table)
    elements.append(Spacer(1, 20))


    # =========================
    # Table II – Key on Ocean state
    # =========================

    elements.append(Paragraph("Table II. Key on Ocean state.", bold_style))
    elements.append(Spacer(1, 10))


    # -------------------------
    # Table II (a)
    # -------------------------

    elements.append(Paragraph("(a)", normal_style))
    elements.append(Spacer(1, 6))

    wave_key_data = [
        ["WAVE HEIGHT RANGE (Meters)", "DESCRIPTION", "IMPACT"],
        [
            "0.6 – 1.0 m (~1.8 – 3.0 ft)",
            Paragraph("Slight", normal_style),
            Paragraph("Conditions Suitable for Marine Activities", normal_style)
        ],

        [
            "1.0 – 1.9 m (~3.0 – 5.7 ft)",
            Paragraph("Slight – Moderate", normal_style),
            Paragraph("Caution on operating marine activities", normal_style)
        ],

        [
            "2.0 – 2.9 m (~6.0 – 8.7 ft)",
            Paragraph("Moderate – Rough", normal_style),
            Paragraph("Caution on operating marine activities", normal_style)
        ],

        [
            "3.0 – 4.0 m (~9.0 – 12.0 ft)",
            Paragraph("Rough", normal_style),
            Paragraph("Warning in place!!!", normal_style)
        ],

        [
            "4.1 – 5.5 m (~12.3 – 16.5 ft)",
            Paragraph("Very Rough", normal_style),
            Paragraph("Warning in place and marine activities on hold", normal_style)
        ]
    ]

    wave_table = Table(
        wave_key_data,
        repeatRows=1,
        colWidths=[doc.width * 0.35, doc.width * 0.2, doc.width * 0.45]
    )

    wave_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('BACKGROUND', (2, 1), (2, 1), colors.green),
        ('BACKGROUND', (2, 2), (2, 3), colors.yellow),
        ('BACKGROUND', (2, 4), (2, 5), colors.red),
    ]))

    elements.append(wave_table)
    elements.append(Spacer(1, 20))


    # -------------------------
    # Table II (b)
    # -------------------------

    elements.append(Paragraph("(b)", normal_style))
    elements.append(Spacer(1, 6))

    wind_key_data = [
        ["WIND RANGE.", "DESCRIPTION.", "IMPACT."],

        [
            "<1 – 7 Knots.",
            Paragraph("Calm to Light breeze.", normal_style),
            Paragraph("1 – 6 Knots; the ocean is relatively calm with very little disturbance. "
            "Suitable for Marine operations", normal_style)
        ],

        [
            "7 – 21 Knots.",
            Paragraph("Gentle breeze to Fresh breeze.", normal_style),
            Paragraph("7 – 17 Knots; Small boats are likely to be filled with water sprays "
            "and become unstable. Caution in carrying out marine activities", normal_style)
        ],

        [
            "22 – ≥34 Knots.",
            Paragraph("Strong breeze to Extremely Strong breeze.", normal_style),
            Paragraph("More than 21 Knots; the ocean state is very much disturbed and the "
            "prevailing conditions are dangerous for marine operations. "
            "Warning in place.", normal_style)
        ]
    ]

    wind_table = Table(
        wind_key_data,
        repeatRows=1,
        colWidths=[doc.width * 0.25, doc.width * 0.25, doc.width * 0.5]
    )

    wind_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('BACKGROUND', (2, 1), (2, 1), colors.green),
        ('BACKGROUND', (2, 2), (2, 2), colors.yellow),
        ('BACKGROUND', (2, 3), (2, 3), colors.red),
    ]))

    elements.append(wind_table)


    elements.append(PageBreak())

    # =========================
    # APPENDIX
    # =========================

    elements.append(Paragraph("APPENDIX 1: INTERPRETATION OF TERMS USED.", bold_style))
    elements.append(Spacer(1, 16))  # More space after main heading

    appendix_table_width = doc.width * 0.98

    def build_appendix_table(table_data, col_ratios):
        col_widths = [appendix_table_width * ratio for ratio in col_ratios]
        
        table = Table(table_data, repeatRows=1, colWidths=col_widths, hAlign="LEFT")
        
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            # Header row bold
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            # First column bold (including header)
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increased from 4
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increased from 4
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return table

    # Table (a)
    elements.append(Paragraph("(a)", normal_style))
    elements.append(Spacer(1, 6))
    rainfall_data = [
        ["Term", "Rainfall Amount [24hrs]", "Description"],
        ["Light", "< 5mm", "Gentle rain, drizzle."],
        ["Moderate", "5 - 20 mm", "Steady, noticeable rain."],
        ["Heavy", "21 - 50 mm", "Intense rain, possible thunder."],
        ["Very Heavy", ">50 mm", "Prolonged rain."],
    ]
    elements.append(build_appendix_table(rainfall_data, [0.33, 0.33, 0.33]))
    elements.append(Spacer(1, 24))  # Extra space before next section

    # Table (b)
    elements.append(Paragraph("(b)", normal_style))
    elements.append(Spacer(1, 6))
    areas_data = [
        ["Term", "Area Affected", "Description"],
        ["Few places", "<33%", "Rain in a small portion of the region."],
        ["Several places", "33% to 66%", "Rain in multiple but not most parts."],
        ["Most places", ">66%", "Rain in nearly all parts."],
    ]
    elements.append(build_appendix_table(areas_data, [0.33, 0.33, 0.33]))
    elements.append(Spacer(1, 24))  # Extra space before next section

    # Table (c)
    elements.append(Paragraph("(c)", normal_style))
    elements.append(Spacer(1, 6))
    probability_data = [
        ["Term", "Probability of Occurrence", "Description"],
        ["Possible", "10 - 30 %", "Low confidence."],
        ["Chance of/ May", "31 - 50 %", "Moderate confidence."],
        ["Likely", "51 - 75 %", "More probable than not."],
        ["Expected", "76 - 90 %", "High confidence."],
        ["Very Likely", "91 - 99 %", "Very high confidence."],
        ["Certain", "100 %", "Guaranteed to occur."],
    ]
    elements.append(build_appendix_table(probability_data, [0.33, 0.33, 0.33]))
    elements.append(PageBreak())

    # =========================
    # SIGN-OFF
    # =========================

    signoff = signoff or {}

    signoff_name = signoff.get("name") or "N/A"
    signoff_title = signoff.get("job_title") or "N/A"
    signoff_mobile = signoff.get("mobile") or "N/A"
    signoff_email = signoff.get("email") or "N/A"

    elements.append(Paragraph(
        "In concurrence with outputs from relevant marine data platforms, acknowledgment is fully accorded to: "
        "ESSO- Indian National Centre for Ocean Information Services (INCOIS), Mercator-ocean.fr, COPERNICUS "
        "Marine Environment Monitoring Service (CMEMS) and other related sources.",
        normal_style
    ))

    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>{signoff_name}</b>", bold_style))
    elements.append(Paragraph(signoff_title, bold_style))
    elements.append(Paragraph(f"Mobile: {signoff_mobile}", bold_style))
    elements.append(Paragraph(f'<font color="blue"><u>Email: {signoff_email}</u></font>', bold_style))

    # =========================
    # BUILD DOCUMENT
    # =========================

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
