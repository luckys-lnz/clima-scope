"""
Enhanced PDF Builder with Improved Formatting

Uses ReportLab's Paragraph, Table, and advanced features for
professional PDF formatting.
"""

import os
from pathlib import Path
from typing import Optional
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
            name='BodyText',
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
            name='Bullet',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=Colors.TEXT_PRIMARY,
            leftIndent=20,
            spaceAfter=8,
            fontName=Fonts.FAMILY_SANS
        ))
        
        # Statistics box text
        self.styles.add(ParagraphStyle(
            name='StatText',
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
        
        # Executive Summary
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
    
    def _build_cover_page(self):
        """Build cover page."""
        story = []
        
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
        period_para = Paragraph(period_text, self.styles['BodyText'])
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
        metadata_para = Paragraph(metadata_text, self.styles['BodyText'])
        story.append(metadata_para)
        story.append(Spacer(1, 1 * cm))
        
        # Disclaimer
        disclaimer_para = Paragraph(
            f"<i>{self.report.cover_page.disclaimer}</i>",
            self.styles['BodyText']
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
            bullet_para = Paragraph(bullet_text, self.styles['Bullet'])
            story.append(bullet_para)
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Weather pattern summary
        summary_para = Paragraph(
            self.report.executive_summary.weather_pattern_summary,
            self.styles['BodyText']
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
            self.styles['BodyText']
        )
        story.append(opening_para)
        story.append(Spacer(1, 0.3 * cm))
        
        # Temporal breakdown
        temp_title = Paragraph("Temporal Breakdown", self.styles['SubsectionHeading'])
        story.append(temp_title)
        
        temporal = self.report.weekly_narrative.temporal_breakdown
        story.append(Paragraph(f"<b>Early Week (Days 1-2):</b> {temporal.early_week}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Mid Week (Days 3-4):</b> {temporal.mid_week}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Late Week (Days 5-7):</b> {temporal.late_week}", self.styles['BodyText']))
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Variable-specific details
        var_title = Paragraph("Variable-Specific Details", self.styles['SubsectionHeading'])
        story.append(var_title)
        
        var_details = self.report.weekly_narrative.variable_specific_details
        story.append(Paragraph(f"<b>Rainfall:</b> {var_details.rainfall}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Temperature:</b> {var_details.temperature}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Wind:</b> {var_details.wind}", self.styles['BodyText']))
        
        if var_details.humidity:
            story.append(Paragraph(f"<b>Humidity:</b> {var_details.humidity}", self.styles['BodyText']))
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Spatial variations
        spatial_title = Paragraph("Spatial Variations", self.styles['SubsectionHeading'])
        story.append(spatial_title)
        story.append(Paragraph(self.report.weekly_narrative.spatial_variations, self.styles['BodyText']))
        
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
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.rainfall_outlook.narrative_description,
            self.styles['BodyText']
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
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Hottest and coolest wards
        hottest_text = f"<b>Hottest Ward:</b> {self.report.temperature_outlook.hottest_ward.ward_name} ({self.report.temperature_outlook.hottest_ward.temperature:.1f}°C)"
        coolest_text = f"<b>Coolest Ward:</b> {self.report.temperature_outlook.coolest_ward.ward_name} ({self.report.temperature_outlook.coolest_ward.temperature:.1f}°C)"
        
        story.append(Paragraph(hottest_text, self.styles['BodyText']))
        story.append(Paragraph(coolest_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.temperature_outlook.narrative_description,
            self.styles['BodyText']
        ))
        
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
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # Narrative
        story.append(Paragraph(
            self.report.wind_outlook.narrative_description,
            self.styles['BodyText']
        ))
        
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
        story.append(Paragraph(events_text, self.styles['BodyText']))
        
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
        story.append(Paragraph(f"<b>Rainfall Impact:</b> {impacts.agricultural_advisories.rainfall_impact}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Temperature Effects:</b> {impacts.agricultural_advisories.temperature_effects}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Optimal Timing:</b> {impacts.agricultural_advisories.optimal_timing}", self.styles['BodyText']))
        story.append(Spacer(1, 0.3 * cm))
        
        # General public advisories
        public_title = Paragraph("General Public Advisories", self.styles['SubsectionHeading'])
        story.append(public_title)
        public = impacts.general_public_advisories
        story.append(Paragraph(f"<b>Travel Conditions:</b> {public.travel_conditions}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Outdoor Activities:</b> {public.outdoor_activity_recommendations}", self.styles['BodyText']))
        story.append(Paragraph(f"<b>Safety Precautions:</b> {public.safety_precautions}", self.styles['BodyText']))
        
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
        story.append(Paragraph(model_text, self.styles['BodyText']))
        
        return story
    
    def _build_metadata_disclaimers(self):
        """Build metadata and disclaimers section."""
        story = []
        
        title = Paragraph("Metadata and Disclaimers", self.styles['SectionHeading'])
        story.append(title)
        
        metadata = self.report.metadata_and_disclaimers
        story.append(Paragraph(metadata.disclaimer_statement, self.styles['BodyText']))
        
        return story
    
    def add_map_image(
        self,
        story: list,
        map_path: Path,
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
                self.styles['BodyText']
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
                    self.styles['Caption'] if 'Caption' in self.styles else self.styles['BodyText']
                ))
            
            story.append(Spacer(1, 0.5 * cm))
            return True
            
        except Exception as e:
            # Log error and use fallback
            error_message = f"Failed to embed map image: {str(e)}"
            fallback_text = fallback_message or f"Map unavailable due to processing error."
            
            story.append(Paragraph(
                f"<i>{fallback_text}</i>",
                self.styles['BodyText']
            ))
            story.append(Spacer(1, 0.5 * cm))
            
            # Don't raise exception, just return False
            return False
    
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
        story.append(Paragraph(placeholder_text, self.styles['BodyText']))
        
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
