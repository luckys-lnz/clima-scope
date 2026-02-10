"""
Enhanced PDF Builder with Improved Formatting

Uses ReportLab's Paragraph, Table, and advanced features for
professional PDF formatting.
"""

import os
from pathlib import Path
from typing import Optional, List, Any
from datetime import date, datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from .models import CompleteWeatherReport
from .config import ReportConfig, Colors, Fonts, Spacing


class MapEmbeddingError(Exception):
    """Exception raised when map embedding fails."""
    pass


class EnhancedPDFBuilder:
    """Enhanced PDF builder with professional formatting."""
    
    def __init__(self, report_data: dict, config: Optional[ReportConfig] = None):
        """
        Initialize enhanced PDF builder.
        
        Args:
            report_data: Dictionary matching CompleteWeatherReport structure
            config: Optional report configuration
        """
        self.report = CompleteWeatherReport(**report_data)
        self.config = config or ReportConfig()
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=Colors.PRIMARY,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=Fonts.FAMILY_SANS
        ))

        # Header style (Kenya Met header)
        self.styles.add(ParagraphStyle(
            name='CustomHeaderCenter',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=Colors.TEXT_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName=Fonts.FAMILY_SANS
        ))
        
        # Heading styles
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=Colors.PRIMARY,
            spaceAfter=12,
            spaceBefore=20,
            fontName=Fonts.FAMILY_SANS
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=Colors.SECONDARY,
            spaceAfter=10,
            spaceBefore=15,
            fontName=Fonts.FAMILY_SANS
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=Colors.TEXT_PRIMARY,
            spaceAfter=12,
            leading=14,
            alignment=TA_JUSTIFY,
            fontName=Fonts.FAMILY_SANS
        ))
        
        # Bullet points
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=Colors.TEXT_PRIMARY,
            leftIndent=20,
            spaceAfter=8,
            fontName=Fonts.FAMILY_SANS
        ))
        
        # Statistics box text
        self.styles.add(ParagraphStyle(
            name='CustomStatText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=Colors.TEXT_PRIMARY,
            spaceAfter=8,
            fontName=Fonts.FAMILY_SANS
        ))
    
    def generate(self, output_path: str) -> str:
        """
        Generate enhanced PDF report.
        
        Args:
            output_path: Path where PDF will be saved
            
        Returns:
            Path to generated PDF file
        """
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.config.page_dimensions,
            rightMargin=self.config.margin_right * cm,
            leftMargin=self.config.margin_left * cm,
            topMargin=self.config.margin_top * cm,
            bottomMargin=self.config.margin_bottom * cm
        )
        
        # Build story (content)
        story = []
        
        # Cover page
        story.extend(self._build_cover_page())
        story.append(PageBreak())
        
        # Kenya Met Format Sections
        story.extend(self._build_kenya_met_part_i())
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_kenya_met_table())
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_kenya_met_marine())
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_kenya_met_appendix())
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_kenya_met_signature())
        story.append(PageBreak())

        # Executive Summary (extended report detail)
        story.extend(self._build_executive_summary())
        story.append(Spacer(1, 0.5 * cm))
        
        # Weekly Narrative
        story.extend(self._build_weekly_narrative())
        story.append(Spacer(1, 0.5 * cm))
        
        # Rainfall Outlook
        story.extend(self._build_rainfall_outlook())
        story.append(Spacer(1, 0.5 * cm))
        
        # Temperature Outlook
        story.extend(self._build_temperature_outlook())
        story.append(Spacer(1, 0.5 * cm))
        
        # Wind Outlook
        story.extend(self._build_wind_outlook())
        story.append(Spacer(1, 0.5 * cm))
        
        # Ward-Level Visualizations
        story.extend(self._build_ward_visualizations())
        story.append(Spacer(1, 0.5 * cm))
        
        # Extreme Values
        story.extend(self._build_extreme_values())
        story.append(Spacer(1, 0.5 * cm))
        
        # Impacts and Advisories
        story.extend(self._build_impacts_advisories())
        story.append(Spacer(1, 0.5 * cm))
        
        # Data Sources and Methodology
        story.extend(self._build_methodology())
        story.append(Spacer(1, 0.5 * cm))
        
        # Metadata and Disclaimers
        story.extend(self._build_metadata_disclaimers())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        return output_path

    def _build_kenya_met_part_i(self):
        """Build Kenya Met Part I summary section."""
        story = []

        title = Paragraph("PART I: Weekly weather forecast summary.", self.styles['SectionHeading'])
        story.append(title)

        highlights = []
        opening = self.report.weekly_narrative.opening_paragraph
        if opening:
            highlights.append(opening)

        # Temperature and wind ranges
        temp = self.report.temperature_outlook.county_level_summary
        wind = self.report.wind_outlook.county_level_summary
        highlights.append(
            f"Maximum/Daytime temperatures are expected to range from "
            f"{temp.minimum_temperature.value:.0f}–{temp.maximum_temperature.value:.0f}°C."
        )
        highlights.append(
            f"Minimum/Night temperatures are expected to range from "
            f"{temp.minimum_temperature.value:.0f}–{temp.maximum_temperature.value:.0f}°C."
        )
        peak_knots = wind.maximum_gust.value * 0.54
        highlights.append(
            f"Moderate to strong {wind.dominant_wind_direction} winds "
            f"({peak_knots:.0f} knots) are expected throughout the week."
        )
        highlights.append(
            "Any significant change in the forecast will be communicated through official channels."
        )

        for line in highlights:
            bullet = Paragraph(f"• {line}", self.styles['CustomBullet'])
            story.append(bullet)

        return story

    def _build_kenya_met_table(self):
        """Build Kenya Met daily forecast table."""
        story = []

        county_name = self.report.cover_page.county.name
        period = self.report.cover_page.report_period
        title_text = (
            f"Table 1: {county_name} County Forecast for "
            f"{period.start_date} to {period.end_date}"
        )
        story.append(Paragraph(title_text, self.styles['SubsectionHeading']))

        days = self._build_day_columns(period.start_date)

        weather_rows = self._build_daily_rows()

        table_data = [
            [""] + days,
            ["Morning"] + weather_rows["morning"],
            ["Afternoon"] + weather_rows["afternoon"],
            ["Night"] + weather_rows["night"],
            ["Rainfall distribution"] + weather_rows["rainfall"],
            ["Maximum temperature (°C)"] + weather_rows["max_temp"],
            ["Minimum temperature (°C)"] + weather_rows["min_temp"],
            ["Winds"] + weather_rows["winds"],
        ]

        col_widths = [3.2 * cm] + [2.4 * cm] * 7
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(table)
        return story

    def _build_kenya_met_marine(self):
        """Build Kenya Met Part II marine weather section."""
        story = []

        title = Paragraph("PART II: 7 days Marine weather.", self.styles['SectionHeading'])
        story.append(title)

        wind = self.report.wind_outlook.county_level_summary
        peak_knots = wind.maximum_gust.value * 0.54
        intro = (
            "Moderate to rough ocean conditions are expected this week. "
            f"Peak gusts up to {peak_knots:.0f} knots."
        )
        story.append(Paragraph(intro, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.2 * cm))

        days = self._build_day_columns(self.report.cover_page.report_period.start_date)
        max_wind = self._build_daily_wind_knots()

        table_data = [
            ["DAYS"] + days,
            ["MAX. Wind (knots)"] + max_wind,
        ]
        table = Table(table_data, colWidths=[3.2 * cm] + [2.4 * cm] * 7)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * cm))

        key_title = Paragraph("Table II: Key on Ocean state.", self.styles['SubsectionHeading'])
        story.append(key_title)

        ocean_key = [
            ["WAVE HEIGHT RANGE (Meters)", "DESCRIPTION", "IMPACT"],
            ["0.6 – 1.0 m", "Slight", "Conditions suitable for marine activities"],
            ["1.0 – 1.9 m", "Slight – Moderate", "Caution on operating marine activities"],
            ["2.0 – 2.9 m", "Moderate – Rough", "Warning in place"],
            ["3.0 – 4.0 m", "Rough", "Warning in place and marine activities on hold"],
            ["4.1 – 5.5 m", "Very Rough", "Warning in place and marine activities on hold"],
        ]
        key_table = Table(ocean_key, colWidths=[4.2 * cm, 4.0 * cm, 7.0 * cm])
        key_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(key_table)
        return story

    def _build_kenya_met_appendix(self):
        """Build appendix with interpretation of terms used."""
        story = []
        title = Paragraph("APPENDIX: Interpretation of Terms Used.", self.styles['SectionHeading'])
        story.append(title)

        rainfall_terms = [
            ["Term", "Rainfall Amount [24hrs]", "Description"],
            ["Light", "< 5mm", "Gentle rain, drizzle."],
            ["Moderate", "5 – 20 mm", "Steady, noticeable rain."],
            ["Heavy", "21 – 50 mm", "Intense rain, possible thunder."],
            ["Very Heavy", "> 50 mm", "Prolonged rain."],
        ]
        rain_table = Table(rainfall_terms, colWidths=[3.0 * cm, 4.0 * cm, 8.2 * cm])
        rain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(rain_table)
        story.append(Spacer(1, 0.3 * cm))

        coverage_terms = [
            ["Term", "Area Affected", "Description"],
            ["Few places", "< 33%", "Rain in a small portion of the region."],
            ["Several places", "33% – 66%", "Rain in multiple but not most parts."],
            ["Most places", "> 66%", "Rain in nearly all parts of the region."],
        ]
        coverage_table = Table(coverage_terms, colWidths=[3.0 * cm, 4.0 * cm, 8.2 * cm])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(coverage_table)
        story.append(Spacer(1, 0.3 * cm))

        probability_terms = [
            ["Term", "Probability of Occurrence", "Description"],
            ["Possible", "10 – 30%", "There is low confidence."],
            ["Chance of/May", "31 – 50%", "There is moderate confidence."],
            ["Likely", "51 – 75%", "The event is more probable than not."],
            ["Expected", "76 – 90%", "There is high confidence."],
            ["Very Likely", "91 – 99%", "There is very high confidence."],
            ["Certain", "100%", "The event is guaranteed to occur."],
        ]
        prob_table = Table(probability_terms, colWidths=[3.2 * cm, 4.2 * cm, 7.8 * cm])
        prob_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(prob_table)
        return story

    def _build_kenya_met_signature(self):
        """Build Kenya Met acknowledgments/signature block."""
        story = []
        text = (
            "In concurrence with outputs from relevant marine data platforms, "
            "acknowledgment is fully accorded to INCOIS, Mercator Ocean, CMEMS "
            "and other related sources."
        )
        story.append(Paragraph(text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("County Director of Meteorological Services.", self.styles['CustomBodyText']))
        return story

    def _build_day_columns(self, start_date: str) -> List[str]:
        """Build day/date column labels from period start date."""
        try:
            base = date.fromisoformat(start_date)
        except ValueError:
            base = date.today()
        return [(base + timedelta(days=i)).strftime("%a\n%d/%m") for i in range(7)]

    def _build_daily_rows(self) -> dict:
        """Build daily row content for Kenya Met forecast table."""
        raw = getattr(self.report, "raw_data", {}) or {}
        vars_ = raw.get("variables", {})
        rain = vars_.get("rainfall", {})
        temp = vars_.get("temperature", {})
        wind = vars_.get("wind", {})

        rainfall_daily = rain.get("daily", [])
        temp_max = temp.get("daily", [])
        temp_min = temp.get("daily_min", [])
        wind_daily = wind.get("daily_peak", [])

        def get_val(arr: List[Any], idx: int, fallback: str) -> str:
            try:
                return f"{float(arr[idx]):.0f}"
            except Exception:
                return fallback

        morning = []
        afternoon = []
        night = []
        rainfall = []
        max_temp = []
        min_temp = []
        winds = []

        for i in range(7):
            rain_val = float(rainfall_daily[i]) if i < len(rainfall_daily) else 0.0
            morning.append("Cloudy with sunny intervals" if rain_val < 5 else "Cloudy with showers")
            afternoon.append("Sunny intervals" if rain_val < 2 else "Sunny intervals and light showers")
            night.append("Partly cloudy night sky")
            rainfall.append("Mostly dry" if rain_val < 1 else "Showers possible in few places")
            max_temp.append(get_val(temp_max, i, "N/A"))
            min_temp.append(get_val(temp_min, i, "N/A"))
            winds.append(self._format_wind_cell(wind_daily, i))

        return {
            "morning": morning,
            "afternoon": afternoon,
            "night": night,
            "rainfall": rainfall,
            "max_temp": max_temp,
            "min_temp": min_temp,
            "winds": winds,
        }

    def _format_wind_cell(self, wind_daily: List[Any], idx: int) -> str:
        """Format wind cell as direction + range in knots."""
        wind_dir = self.report.wind_outlook.county_level_summary.dominant_wind_direction
        try:
            speed_kmh = float(wind_daily[idx])
        except Exception:
            speed_kmh = self.report.wind_outlook.county_level_summary.mean_wind_speed
        speed_knots = speed_kmh * 0.54
        low = max(1, round(speed_knots - 3))
        high = max(low + 1, round(speed_knots + 3))
        return f"{wind_dir} winds\n{low}-{high} knots"

    def _build_daily_wind_knots(self) -> List[str]:
        """Build list of daily max wind speeds in knots."""
        raw = getattr(self.report, "raw_data", {}) or {}
        wind = raw.get("variables", {}).get("wind", {})
        daily = wind.get("daily_peak", [])
        result = []
        for i in range(7):
            try:
                kmh = float(daily[i])
                knots = round(kmh * 0.54)
                result.append(str(knots))
            except Exception:
                result.append("N/A")
        return result
    
    def _build_cover_page(self):
        """Build cover page."""
        story = []

        header_lines = [
            "REPUBLIC OF KENYA",
            "MINISTRY OF ENVIRONMENT CLIMATE CHANGE AND FORESTRY",
            "KENYA METEOROLOGICAL DEPARTMENT",
        ]
        for line in header_lines:
            story.append(Paragraph(line, self.styles['CustomHeaderCenter']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{self.report.cover_page.county.name} County Meteorological Office", self.styles['CustomHeaderCenter']))
        story.append(Spacer(1, 0.6 * cm))
        issue_date = datetime.utcnow().strftime("%d %b %Y")
        period = self.report.cover_page.report_period
        period_line = f"{period.start_date} to {period.end_date}"
        story.append(Paragraph(f"Date of issue: {issue_date}", self.styles['CustomHeaderCenter']))
        story.append(Paragraph(f"Period of forecast: {period_line}", self.styles['CustomHeaderCenter']))
        story.append(Spacer(1, 0.6 * cm))
        
        # Title
        title = Paragraph(self.report.cover_page.report_title, self.styles['CustomTitle'])
        story.append(Spacer(1, 8 * cm))
        story.append(title)
        story.append(Spacer(1, 1 * cm))
        
        # County name
        county_text = f"{self.report.cover_page.county.name} County"
        county_para = Paragraph(county_text, self.styles['SectionHeading'])
        story.append(county_para)
        story.append(Spacer(1, 0.5 * cm))
        
        # Report period
        period_text = self.report.cover_page.report_period.formatted
        period_para = Paragraph(period_text, self.styles['CustomBodyText'])
        story.append(period_para)
        story.append(Spacer(1, 3 * cm))
        
        # Metadata
        metadata = self.report.cover_page.generation_metadata
        metadata_text = f"""
        <b>Data Source:</b> {metadata.data_source}<br/>
        <b>Model Run:</b> {metadata.model_run_timestamp}<br/>
        <b>Generated:</b> {metadata.generated_at}<br/>
        <b>System Version:</b> {metadata.system_version}
        """
        metadata_para = Paragraph(metadata_text, self.styles['CustomBodyText'])
        story.append(metadata_para)
        story.append(Spacer(1, 1 * cm))
        
        # Disclaimer
        disclaimer_para = Paragraph(
            f"<i>{self.report.cover_page.disclaimer}</i>",
            self.styles['CustomBodyText']
        )
        story.append(disclaimer_para)
        
        return story
    
    def _build_executive_summary(self):
        """Build executive summary section."""
        story = []
        
        # Section title
        title = Paragraph("Executive Summary", self.styles['SectionHeading'])
        story.append(title)
        
        # Statistics box
        stats = self.report.executive_summary.summary_statistics
        stats_data = [
            ['Total Rainfall:', f"{stats.total_rainfall:.1f} mm"],
            ['Mean Temperature:', f"{stats.mean_temperature:.1f}°C"],
            ['Temperature Range:', f"{stats.temperature_range.min:.1f}°C - {stats.temperature_range.max:.1f}°C"],
            ['Max Wind Speed:', f"{stats.max_wind_speed:.1f} km/h"],
            ['Dominant Wind Direction:', stats.dominant_wind_direction]
        ]
        
        stats_table = Table(stats_data, colWidths=[6 * cm, 8 * cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), Colors.BG_LIGHT),
            ('TEXTCOLOR', (0, 0), (-1, -1), Colors.TEXT_PRIMARY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, Colors.TEXT_LIGHT),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5 * cm))
        
        # Key highlights
        highlights_title = Paragraph("Key Highlights", self.styles['SubsectionHeading'])
        story.append(highlights_title)
        
        for highlight in self.report.executive_summary.key_highlights:
            bullet_text = f"• {highlight}"
            bullet_para = Paragraph(bullet_text, self.styles['CustomBullet'])
            story.append(bullet_para)
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Weather pattern summary
        summary_para = Paragraph(
            self.report.executive_summary.weather_pattern_summary,
            self.styles['CustomBodyText']
        )
        story.append(summary_para)
        
        return story
    
    def _build_weekly_narrative(self):
        """Build weekly narrative section."""
        story = []
        
        title = Paragraph("Weekly Narrative Summary", self.styles['SectionHeading'])
        story.append(title)
        
        # Opening paragraph
        opening_para = Paragraph(
            self.report.weekly_narrative.opening_paragraph,
            self.styles['CustomBodyText']
        )
        story.append(opening_para)
        story.append(Spacer(1, 0.3 * cm))
        
        # Temporal breakdown
        temp_title = Paragraph("Temporal Breakdown", self.styles['SubsectionHeading'])
        story.append(temp_title)
        
        temporal = self.report.weekly_narrative.temporal_breakdown
        story.append(Paragraph(f"<b>Early Week (Days 1-2):</b> {temporal.early_week}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Mid Week (Days 3-4):</b> {temporal.mid_week}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Late Week (Days 5-7):</b> {temporal.late_week}", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Variable-specific details
        var_title = Paragraph("Variable-Specific Details", self.styles['SubsectionHeading'])
        story.append(var_title)
        
        var_details = self.report.weekly_narrative.variable_specific_details
        story.append(Paragraph(f"<b>Rainfall:</b> {var_details.rainfall}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Temperature:</b> {var_details.temperature}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Wind:</b> {var_details.wind}", self.styles['CustomBodyText']))
        
        if var_details.humidity:
            story.append(Paragraph(f"<b>Humidity:</b> {var_details.humidity}", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Spatial variations
        spatial_title = Paragraph("Spatial Variations", self.styles['SubsectionHeading'])
        story.append(spatial_title)
        story.append(Paragraph(self.report.weekly_narrative.spatial_variations, self.styles['CustomBodyText']))
        
        return story
    
    def _build_rainfall_outlook(self):
        """Build rainfall outlook section."""
        story = []
        
        title = Paragraph("Rainfall Outlook", self.styles['SectionHeading'])
        story.append(title)
        
        # County summary
        summary = self.report.rainfall_outlook.county_level_summary
        summary_text = f"""
        <b>Total Weekly Rainfall:</b> {summary.total_weekly_rainfall:.1f} mm<br/>
        <b>Rainy Days:</b> {summary.number_of_rainy_days}<br/>
        <b>Max Daily Intensity:</b> {summary.max_daily_intensity:.1f} mm
        """
        story.append(Paragraph(summary_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.rainfall_outlook.narrative_description,
            self.styles['CustomBodyText']
        ))
        story.append(Spacer(1, 0.3 * cm))
        
        # Top wards table
        wards_title = Paragraph("Top Wards by Rainfall", self.styles['SubsectionHeading'])
        story.append(wards_title)
        
        wards_data = [['Ward', 'Total Rainfall (mm)']]
        for ward in self.report.rainfall_outlook.top_wards_by_rainfall[:10]:
            wards_data.append([ward.ward_name, f"{ward.total_rainfall:.1f}"])
        
        wards_table = Table(wards_data, colWidths=[10 * cm, 4 * cm])
        wards_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), Colors.TEXT_PRIMARY),
            ('FONTNAME', (0, 1), (-1, -1), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, Colors.TEXT_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Colors.BG_LIGHT]),
        ]))
        story.append(wards_table)
        story.append(Spacer(1, 0.4 * cm))

        # Rainfall distribution map
        map_info = self.report.rainfall_outlook.rainfall_distribution_map
        map_path = self._resolve_map_path(map_info.image_path)
        caption = self._format_color_scale_caption(map_info.color_scale)
        self.add_map_image(
            story=story,
            map_path=map_path,
            title="Rainfall Distribution Map",
            caption=caption,
            fallback_message="Rainfall map not available yet. It will be added once geospatial processing completes."
        )
        
        return story
    
    def _build_temperature_outlook(self):
        """Build temperature outlook section."""
        story = []
        
        title = Paragraph("Temperature Outlook", self.styles['SectionHeading'])
        story.append(title)
        
        summary = self.report.temperature_outlook.county_level_summary
        summary_text = f"""
        <b>Mean Weekly Temperature:</b> {summary.mean_weekly_temperature:.1f}°C<br/>
        <b>Range:</b> {summary.minimum_temperature.value:.1f}°C - {summary.maximum_temperature.value:.1f}°C
        """
        story.append(Paragraph(summary_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Hottest and coolest wards
        hottest_text = f"<b>Hottest Ward:</b> {self.report.temperature_outlook.hottest_ward.ward_name} ({self.report.temperature_outlook.hottest_ward.temperature:.1f}°C)"
        coolest_text = f"<b>Coolest Ward:</b> {self.report.temperature_outlook.coolest_ward.ward_name} ({self.report.temperature_outlook.coolest_ward.temperature:.1f}°C)"
        
        story.append(Paragraph(hottest_text, self.styles['CustomBodyText']))
        story.append(Paragraph(coolest_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.temperature_outlook.narrative_description,
            self.styles['CustomBodyText']
        ))
        story.append(Spacer(1, 0.4 * cm))

        # Temperature distribution map
        map_info = self.report.temperature_outlook.temperature_distribution_map
        map_path = self._resolve_map_path(map_info.image_path)
        caption = self._format_color_scale_caption(map_info.color_scale)
        self.add_map_image(
            story=story,
            map_path=map_path,
            title="Temperature Distribution Map",
            caption=caption,
            fallback_message="Temperature map not available yet. It will be added once geospatial processing completes."
        )
        
        return story
    
    def _build_wind_outlook(self):
        """Build wind outlook section."""
        story = []
        
        title = Paragraph("Wind Outlook", self.styles['SectionHeading'])
        story.append(title)
        
        summary = self.report.wind_outlook.county_level_summary
        summary_text = f"""
        <b>Mean Wind Speed:</b> {summary.mean_wind_speed:.1f} km/h<br/>
        <b>Max Gust:</b> {summary.maximum_gust.value:.1f} km/h<br/>
        <b>Dominant Direction:</b> {summary.dominant_wind_direction}
        """
        story.append(Paragraph(summary_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.wind_outlook.narrative_description,
            self.styles['CustomBodyText']
        ))
        story.append(Spacer(1, 0.4 * cm))

        # Wind speed distribution map
        map_info = self.report.wind_outlook.wind_speed_distribution_map
        map_path = self._resolve_map_path(map_info.image_path)
        caption = self._format_color_scale_caption(map_info.color_scale)
        self.add_map_image(
            story=story,
            map_path=map_path,
            title="Wind Speed Distribution Map",
            caption=caption,
            fallback_message="Wind map not available yet. It will be added once geospatial processing completes."
        )
        
        return story

    def _build_ward_visualizations(self):
        """Build ward-level visualizations section."""
        story = []

        title = Paragraph("Ward-Level Visualizations", self.styles['SectionHeading'])
        story.append(title)

        ward_maps = self.report.ward_level_visualizations

        # Rainfall ward map
        rain_path = self._resolve_map_path(ward_maps.rainfall_map.image_path)
        self.add_map_image(
            story=story,
            map_path=rain_path,
            title=ward_maps.rainfall_map.title or "Ward-Level Rainfall Map",
            caption=f"Resolution: {ward_maps.rainfall_map.resolution}. Projection: {ward_maps.rainfall_map.projection}.",
            fallback_message="Ward-level rainfall map not available yet."
        )

        # Temperature ward map
        temp_path = self._resolve_map_path(ward_maps.temperature_map.image_path)
        self.add_map_image(
            story=story,
            map_path=temp_path,
            title=ward_maps.temperature_map.title or "Ward-Level Temperature Map",
            caption=f"Resolution: {ward_maps.temperature_map.resolution}. Projection: {ward_maps.temperature_map.projection}.",
            fallback_message="Ward-level temperature map not available yet."
        )

        # Wind ward map
        wind_path = self._resolve_map_path(ward_maps.wind_speed_map.image_path)
        self.add_map_image(
            story=story,
            map_path=wind_path,
            title=ward_maps.wind_speed_map.title or "Ward-Level Wind Speed Map",
            caption=f"Resolution: {ward_maps.wind_speed_map.resolution}. Projection: {ward_maps.wind_speed_map.projection}.",
            fallback_message="Ward-level wind map not available yet."
        )

        return story
    
    def _build_extreme_values(self):
        """Build extreme values section."""
        story = []
        
        title = Paragraph("Extreme Values and Highlights", self.styles['SectionHeading'])
        story.append(title)
        
        events = self.report.extreme_values.extreme_events
        
        events_text = f"""
        <b>Highest Single Day Rainfall:</b> {events.highest_single_day_rainfall.ward_name} - {events.highest_single_day_rainfall.value:.1f} mm<br/>
        <b>Highest Weekly Rainfall:</b> {events.highest_weekly_rainfall.ward_name} - {events.highest_weekly_rainfall.total:.1f} mm<br/>
        <b>Hottest Day:</b> {events.hottest_day.ward_name} - {events.hottest_day.temperature:.1f}°C<br/>
        <b>Coolest Night:</b> {events.coolest_night.ward_name} - {events.coolest_night.temperature:.1f}°C<br/>
        <b>Strongest Wind Gust:</b> {events.strongest_wind_gust.ward_name} - {events.strongest_wind_gust.speed:.1f} km/h
        """
        story.append(Paragraph(events_text, self.styles['CustomBodyText']))
        
        return story
    
    def _build_impacts_advisories(self):
        """Build impacts and advisories section."""
        story = []
        
        title = Paragraph("Impacts and Advisories", self.styles['SectionHeading'])
        story.append(title)
        
        impacts = self.report.impacts_and_advisories
        
        # Agricultural advisories
        ag_title = Paragraph("Agricultural Advisories", self.styles['SubsectionHeading'])
        story.append(ag_title)
        story.append(Paragraph(f"<b>Rainfall Impact:</b> {impacts.agricultural_advisories.rainfall_impact}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Temperature Effects:</b> {impacts.agricultural_advisories.temperature_effects}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Optimal Timing:</b> {impacts.agricultural_advisories.optimal_timing}", self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # General public advisories
        public_title = Paragraph("General Public Advisories", self.styles['SubsectionHeading'])
        story.append(public_title)
        public = impacts.general_public_advisories
        story.append(Paragraph(f"<b>Travel Conditions:</b> {public.travel_conditions}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Outdoor Activities:</b> {public.outdoor_activity_recommendations}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Safety Precautions:</b> {public.safety_precautions}", self.styles['CustomBodyText']))
        
        return story
    
    def _build_methodology(self):
        """Build data sources and methodology section."""
        story = []
        
        title = Paragraph("Data Sources and Methodology", self.styles['SectionHeading'])
        story.append(title)
        
        methodology = self.report.data_sources_and_methodology
        model = methodology.forecast_model
        
        model_text = f"""
        <b>Forecast Model:</b> {model.name} {model.version}<br/>
        <b>Grid Resolution:</b> {model.grid_resolution}<br/>
        <b>Forecast Horizon:</b> {model.forecast_horizon} days
        """
        story.append(Paragraph(model_text, self.styles['CustomBodyText']))
        
        return story
    
    def _build_metadata_disclaimers(self):
        """Build metadata and disclaimers section."""
        story = []
        
        title = Paragraph("Metadata and Disclaimers", self.styles['SectionHeading'])
        story.append(title)
        
        metadata = self.report.metadata_and_disclaimers
        story.append(Paragraph(metadata.disclaimer_statement, self.styles['CustomBodyText']))
        
        return story
    
    def add_map_image(
        self,
        story: list,
        map_path: Optional[Path],
        title: str = "Map",
        caption: Optional[str] = None,
        max_width: float = 15.0,  # cm
        max_height: float = 12.0,  # cm
        dpi: int = 300,
        fallback_message: Optional[str] = None
    ) -> bool:
        """
        Add a map image to the PDF story with proper scaling and fallback.
        
        Args:
            story: ReportLab story list to append to
            map_path: Path to the map image file
            title: Title/heading for the map section
            caption: Optional caption text below the map
            max_width: Maximum width in centimeters
            max_height: Maximum height in centimeters
            dpi: Expected DPI of the image
            fallback_message: Message to display if image missing
            
        Returns:
            True if image added successfully, False if fallback used
            
        Raises:
            MapEmbeddingError: If image processing fails critically
        """
        # Add title
        if title:
            story.append(Paragraph(title, self.styles['SubsectionHeading']))
            story.append(Spacer(1, 0.2 * cm))
        
        # Check if map file exists
        if not map_path or not Path(map_path).exists():
            # Use fallback
            fallback_text = fallback_message or (
                f"Map not available. The {title.lower()} will be generated "
                "when geospatial processing is complete."
            )
            story.append(Paragraph(
                f"<i>{fallback_text}</i>",
                self.styles['CustomBodyText']
            ))
            story.append(Spacer(1, 0.5 * cm))
            return False
        
        try:
            # Create Image object with automatic sizing
            img = Image(str(map_path))
            
            # Get original dimensions
            img_width, img_height = img.imageWidth, img.imageHeight
            
            # Calculate scaling to fit within max dimensions
            # while preserving aspect ratio
            width_scale = (max_width * cm) / img_width
            height_scale = (max_height * cm) / img_height
            scale = min(width_scale, height_scale)
            
            # Apply scaling
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale
            
            # Add image to story
            story.append(img)
            story.append(Spacer(1, 0.2 * cm))
            
            # Add caption if provided
            if caption:
                story.append(Paragraph(
                    f"<i>{caption}</i>",
                self.styles['Caption'] if 'Caption' in self.styles else self.styles['CustomBodyText']
                ))
            
            story.append(Spacer(1, 0.5 * cm))
            return True
            
        except Exception as e:
            # Log error and use fallback
            error_message = f"Failed to embed map image: {str(e)}"
            fallback_text = fallback_message or f"Map unavailable due to processing error."
            
            story.append(Paragraph(
                f"<i>{fallback_text}</i>",
                self.styles['CustomBodyText']
            ))
            story.append(Spacer(1, 0.5 * cm))
            
            # Don't raise exception, just return False
            return False

    def _resolve_map_path(self, image_path: Optional[str]) -> Optional[Path]:
        """Resolve image paths that may be relative to repo root or storage."""
        if not image_path:
            return None

        candidate = Path(image_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        repo_root = Path(__file__).resolve().parents[1]
        repo_candidate = repo_root / image_path
        if repo_candidate.exists():
            return repo_candidate

        storage_candidate = repo_root / "storage" / image_path
        if storage_candidate.exists():
            return storage_candidate

        data_candidate = repo_root / "data" / image_path
        if data_candidate.exists():
            return data_candidate

        return None

    def _format_color_scale_caption(self, color_scale: Optional[List]) -> Optional[str]:
        """Format a short caption from a color scale."""
        if not color_scale:
            return None
        try:
            parts = [f"{item.range}: {item.color}" for item in color_scale]
        except Exception:
            return None
        return "Color scale: " + "; ".join(parts)
    
    def add_map_placeholder(
        self,
        story: list,
        variable: str,
        county_name: str,
        period: str
    ):
        """
        Add a placeholder for a map that will be provided by Person A.
        
        Args:
            story: ReportLab story list
            variable: Weather variable (rainfall, temperature, wind)
            county_name: County name
            period: Period string (e.g., "2026-01-27 to 2026-02-02")
        """
        title = f"{variable.title()} Distribution Map"
        story.append(Paragraph(title, self.styles['SubsectionHeading']))
        story.append(Spacer(1, 0.2 * cm))
        
        # Create placeholder box
        placeholder_text = f"""
        <i>Map Placeholder: {variable.title()} distribution for {county_name} County<br/>
        Period: {period}<br/><br/>
        This map will be generated by the geospatial processing pipeline and embedded here.<br/>
        Expected format: PNG, 1200x900px, 300 DPI</i>
        """
        story.append(Paragraph(placeholder_text, self.styles['CustomBodyText']))
        
        # Add visual placeholder (colored box)
        placeholder_data = [[f"[{variable.upper()} MAP]"]]
        placeholder_table = Table(placeholder_data, colWidths=[12 * cm], rowHeights=[8 * cm])
        placeholder_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), Fonts.FAMILY_SANS),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('BOX', (0, 0), (-1, -1), 2, colors.darkgrey),
        ]))
        story.append(placeholder_table)
        story.append(Spacer(1, 0.5 * cm))
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        # Header
        canvas_obj.saveState()
        canvas_obj.setFont(Fonts.FAMILY_SANS, 9)
        canvas_obj.setFillColor(Colors.TEXT_SECONDARY)
        
        county_name = self.report.cover_page.county.name
        header_text = f"Weekly Weather Outlook - {county_name} County"
        canvas_obj.drawString(
            self.config.margin_left * cm,
            doc.height + doc.topMargin + 0.5 * cm,
            header_text
        )
        
        # Footer
        page_num = canvas_obj.getPageNumber()
        footer_text = f"Page {page_num}"
        text_width = canvas_obj.stringWidth(footer_text, Fonts.FAMILY_SANS, 9)
        canvas_obj.drawString(
            doc.width + doc.leftMargin - text_width,
            1 * cm,
            footer_text
        )
        
        canvas_obj.restoreState()


if __name__ == "__main__":
    print("="*70)
    print("ERROR: This module should not be run directly")
    print("="*70)
    print("\nThis is a library module. To generate PDFs, use one of these methods:\n")
    print("1. Using the AI-powered generation script:")
    print("   cd pdf_generator")
    print("   python generate_ai_sample.py")
    print()
    print("2. Using the sample generation script:")
    print("   cd pdf_generator")
    print("   python generate_sample.py")
    print()
    print("3. As a Python module:")
    print("   python -m pdf_generator.generate_ai_sample")
    print()
    print("4. In your own code:")
    print("   from pdf_generator import EnhancedPDFBuilder")
    print("   builder = EnhancedPDFBuilder(complete_report)")
    print("   builder.generate('output.pdf')")
    print()
    print("See pdf_generator/README.md for more details.")
    print("="*70)
    import sys
    sys.exit(1)
