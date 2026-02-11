"""
Section Generators for PDF Report

Each class generates a specific section of the weather report.
"""

from typing import TYPE_CHECKING
from reportlab.lib.units import cm
from reportlab.lib import colors

from .config import ReportConfig, Colors, Fonts, Spacing
from .utils import (
    format_date, format_temperature, format_rainfall, format_wind_speed,
    format_percentage, split_text_into_lines, get_risk_level_color
)

if TYPE_CHECKING:
    from reportlab.pdfgen import canvas
    from .models import (
        CoverPageInfo, ExecutiveSummary, WeeklyNarrative,
        RainfallOutlook, TemperatureOutlook, WindOutlook,
        WardLevelVisualizations, ExtremeValues, ImpactsAndAdvisories,
        DataSourcesAndMethodology, MetadataAndDisclaimers
    )


class BaseSectionGenerator:
    """Base class for all section generators."""
    
    def __init__(self, config: ReportConfig):
        """Initialize section generator with configuration."""
        self.config = config
        self.content_width = config.content_width
        self.margin_left = config.margin_left * cm
        self.margin_bottom = config.margin_bottom * cm
    
    def _draw_section_title(self, canvas: "canvas.Canvas", title: str, y: float) -> float:
        """Draw section title and return new y position."""
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H2_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, title)
        
        # Draw underline
        canvas.setStrokeColor(Colors.PRIMARY)
        canvas.setLineWidth(2)
        canvas.line(
            self.margin_left,
            y - 0.2 * cm,
            self.margin_left + self.content_width * 0.4,
            y - 0.2 * cm
        )
        
        return y - (Spacing.SECTION_SPACING * cm)
    
    def _draw_paragraph(self, canvas: "canvas.Canvas", text: str, y: float, 
                       font_size: int = Fonts.BODY_SIZE) -> float:
        """Draw paragraph text and return new y position."""
        canvas.setFont(Fonts.FAMILY_SANS, font_size)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        
        lines = split_text_into_lines(text, self.content_width, font_size)
        line_height = font_size * 1.2
        
        for line in lines:
            canvas.drawString(self.margin_left, y, line)
            y -= line_height
        
        return y - (Spacing.PARAGRAPH_SPACING * cm)


class CoverPageGenerator(BaseSectionGenerator):
    """Generator for cover page section."""
    
    def generate(self, canvas: "canvas.Canvas", cover_page: "CoverPageInfo", start_y: float) -> float:
        """Generate cover page."""
        y = start_y
        
        # Title
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H1_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        title_lines = split_text_into_lines(
            cover_page.report_title,
            self.content_width,
            Fonts.H1_SIZE
        )
        
        title_y = self.config.page_height / 2 + (len(title_lines) * Fonts.H1_SIZE * 1.5) / 2
        for line in title_lines:
            text_width = canvas.stringWidth(line, Fonts.FAMILY_SANS, Fonts.H1_SIZE)
            x = (self.config.page_width - text_width) / 2
            canvas.drawString(x, title_y, line)
            title_y -= Fonts.H1_SIZE * 1.5
        
        # County name
        y = title_y - (2 * cm)
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H2_SIZE)
        canvas.setFillColor(Colors.SECONDARY)
        county_text = f"{cover_page.county.name} County"
        text_width = canvas.stringWidth(county_text, Fonts.FAMILY_SANS, Fonts.H2_SIZE)
        x = (self.config.page_width - text_width) / 2
        canvas.drawString(x, y, county_text)
        
        # Report period
        y -= (1.5 * cm)
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        period_text = cover_page.report_period.formatted
        text_width = canvas.stringWidth(period_text, Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        x = (self.config.page_width - text_width) / 2
        canvas.drawString(x, y, period_text)
        
        # Metadata (bottom of page)
        y = 3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.SMALL_SIZE)
        canvas.setFillColor(Colors.TEXT_SECONDARY)
        
        metadata_lines = [
            f"Data Source: {cover_page.generation_metadata.data_source}",
            f"Model Run: {format_date(cover_page.generation_metadata.model_run_timestamp)}",
            f"Generated: {format_date(cover_page.generation_metadata.generated_at)}",
            f"System Version: {cover_page.generation_metadata.system_version}",
        ]
        
        for line in metadata_lines:
            canvas.drawString(self.margin_left, y, line)
            y -= Fonts.SMALL_SIZE * 1.3
        
        # Disclaimer
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.TINY_SIZE)
        canvas.setFillColor(Colors.TEXT_LIGHT)
        disclaimer_lines = split_text_into_lines(
            cover_page.disclaimer,
            self.content_width,
            Fonts.TINY_SIZE
        )
        for line in disclaimer_lines:
            canvas.drawString(self.margin_left, y, line)
            y -= Fonts.TINY_SIZE * 1.2
        
        return y


class ExecutiveSummaryGenerator(BaseSectionGenerator):
    """Generator for executive summary section."""
    
    def generate(self, canvas: "canvas.Canvas", summary: "ExecutiveSummary", start_y: float) -> float:
        """Generate executive summary section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Executive Summary", y)
        
        # Summary statistics box
        y = self._draw_statistics_box(canvas, summary.summary_statistics, y)
        
        # Key highlights
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H3_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Key Highlights")
        y -= 0.3 * cm
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        for highlight in summary.key_highlights:
            # Bullet point
            canvas.drawString(self.margin_left, y, "•")
            # Text
            text_x = self.margin_left + 0.3 * cm
            lines = split_text_into_lines(highlight, self.content_width - 0.3 * cm, Fonts.BODY_SIZE)
            for line in lines:
                canvas.drawString(text_x, y, line)
                y -= Fonts.BODY_SIZE * 1.2
            y -= 0.2 * cm
        
        # Weather pattern summary
        y -= 0.3 * cm
        y = self._draw_paragraph(canvas, summary.weather_pattern_summary, y)
        
        return y
    
    def _draw_statistics_box(self, canvas: "canvas.Canvas", stats, y: float) -> float:
        """Draw statistics in a box."""
        box_height = 3 * cm
        box_y = y - box_height
        
        # Draw box
        canvas.setStrokeColor(Colors.PRIMARY)
        canvas.setFillColor(Colors.BG_LIGHT)
        canvas.setLineWidth(1)
        canvas.rect(self.margin_left, box_y, self.content_width, box_height, fill=1, stroke=1)
        
        # Statistics
        stat_y = y - 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        
        stats_text = [
            f"Total Rainfall: {format_rainfall(stats.total_rainfall)}",
            f"Mean Temperature: {format_temperature(stats.mean_temperature)}",
            f"Temperature Range: {format_temperature(stats.temperature_range.min)} - {format_temperature(stats.temperature_range.max)}",
            f"Max Wind Speed: {format_wind_speed(stats.max_wind_speed)}",
            f"Dominant Wind Direction: {stats.dominant_wind_direction}",
        ]
        
        for text in stats_text:
            canvas.drawString(self.margin_left + 0.3 * cm, stat_y, text)
            stat_y -= Fonts.BODY_SIZE * 1.3
        
        return box_y - (Spacing.SECTION_SPACING * cm)


class WeeklyNarrativeGenerator(BaseSectionGenerator):
    """Generator for weekly narrative section."""
    
    def generate(self, canvas: "canvas.Canvas", narrative: "WeeklyNarrative", start_y: float) -> float:
        """Generate weekly narrative section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Weekly Narrative Summary", y)
        
        # Opening paragraph
        y = self._draw_paragraph(canvas, narrative.opening_paragraph, y)
        
        # Temporal breakdown
        y -= 0.3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Temporal Breakdown")
        y -= 0.2 * cm
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        
        temporal_items = [
            ("Early Week (Days 1-2):", narrative.temporal_breakdown.early_week),
            ("Mid Week (Days 3-4):", narrative.temporal_breakdown.mid_week),
            ("Late Week (Days 5-7):", narrative.temporal_breakdown.late_week),
        ]
        
        for label, text in temporal_items:
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.SECONDARY)
            canvas.drawString(self.margin_left, y, label)
            y -= Fonts.BODY_SIZE * 1.2
            
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.TEXT_PRIMARY)
            y = self._draw_paragraph(canvas, text, y)
            y -= 0.2 * cm
        
        # Variable-specific details
        y -= 0.3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Variable-Specific Details")
        y -= 0.2 * cm
        
        var_details = [
            ("Rainfall:", narrative.variable_specific_details.rainfall),
            ("Temperature:", narrative.variable_specific_details.temperature),
            ("Wind:", narrative.variable_specific_details.wind),
        ]
        
        if narrative.variable_specific_details.humidity:
            var_details.append(("Humidity:", narrative.variable_specific_details.humidity))
        
        for label, text in var_details:
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.SECONDARY)
            canvas.drawString(self.margin_left, y, label)
            y -= Fonts.BODY_SIZE * 1.2
            
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.TEXT_PRIMARY)
            y = self._draw_paragraph(canvas, text, y)
            y -= 0.2 * cm
        
        # Spatial variations
        y -= 0.3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Spatial Variations")
        y -= 0.2 * cm
        
        y = self._draw_paragraph(canvas, narrative.spatial_variations, y)
        
        return y


class RainfallOutlookGenerator(BaseSectionGenerator):
    """Generator for rainfall outlook section."""
    
    def generate(self, canvas: "canvas.Canvas", outlook: "RainfallOutlook", start_y: float) -> float:
        """Generate rainfall outlook section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Rainfall Outlook", y)
        
        # County-level summary
        y = self._draw_rainfall_summary(canvas, outlook.county_level_summary, y)
        
        # Narrative description
        y = self._draw_paragraph(canvas, outlook.narrative_description, y)
        
        # Top wards table (simplified - full implementation would use Table)
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Top Wards by Rainfall")
        y -= 0.3 * cm
        
        # Simple table header
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.TABLE_HEADER_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Ward")
        canvas.drawString(self.margin_left + 8 * cm, y, "Total Rainfall")
        y -= 0.3 * cm
        
        # Table rows
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.TABLE_CELL_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        for ward in outlook.top_wards_by_rainfall[:10]:  # Top 10
            canvas.drawString(self.margin_left, y, ward.ward_name)
            canvas.drawString(self.margin_left + 8 * cm, y, format_rainfall(ward.total_rainfall))
            y -= Fonts.TABLE_CELL_SIZE * 1.2
        
        return y
    
    def _draw_rainfall_summary(self, canvas: "canvas.Canvas", summary, y: float) -> float:
        """Draw rainfall summary box."""
        # Summary text
        summary_text = (
            f"Total Weekly Rainfall: {format_rainfall(summary.total_weekly_rainfall)} | "
            f"Rainy Days: {summary.number_of_rainy_days} | "
            f"Max Daily Intensity: {format_rainfall(summary.max_daily_intensity)}"
        )
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        canvas.drawString(self.margin_left, y, summary_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        return y


class TemperatureOutlookGenerator(BaseSectionGenerator):
    """Generator for temperature outlook section."""
    
    def generate(self, canvas: "canvas.Canvas", outlook: "TemperatureOutlook", start_y: float) -> float:
        """Generate temperature outlook section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Temperature Outlook", y)
        
        # County-level summary
        summary = outlook.county_level_summary
        summary_text = (
            f"Mean Weekly Temperature: {format_temperature(summary.mean_weekly_temperature)} | "
            f"Range: {format_temperature(summary.minimum_temperature.value)} - "
            f"{format_temperature(summary.maximum_temperature.value)}"
        )
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        canvas.drawString(self.margin_left, y, summary_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        # Hottest and coolest wards
        y -= 0.3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        hottest_text = (
            f"Hottest Ward: {outlook.hottest_ward.ward_name} "
            f"({format_temperature(outlook.hottest_ward.temperature)})"
        )
        coolest_text = (
            f"Coolest Ward: {outlook.coolest_ward.ward_name} "
            f"({format_temperature(outlook.coolest_ward.temperature)})"
        )
        
        canvas.drawString(self.margin_left, y, hottest_text)
        y -= Fonts.BODY_SIZE * 1.2
        canvas.drawString(self.margin_left, y, coolest_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        # Narrative description
        y = self._draw_paragraph(canvas, outlook.narrative_description, y)
        
        return y


class WindOutlookGenerator(BaseSectionGenerator):
    """Generator for wind outlook section."""
    
    def generate(self, canvas: "canvas.Canvas", outlook: "WindOutlook", start_y: float) -> float:
        """Generate wind outlook section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Wind Outlook", y)
        
        # County-level summary
        summary = outlook.county_level_summary
        summary_text = (
            f"Mean Wind Speed: {format_wind_speed(summary.mean_wind_speed)} | "
            f"Max Gust: {format_wind_speed(summary.maximum_gust.value)} | "
            f"Dominant Direction: {summary.dominant_wind_direction}"
        )
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        canvas.drawString(self.margin_left, y, summary_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        # Narrative description
        y = self._draw_paragraph(canvas, outlook.narrative_description, y)
        
        return y


class WardVisualizationsGenerator(BaseSectionGenerator):
    """Generator for ward-level visualizations section."""
    
    def generate(self, canvas: "canvas.Canvas", visualizations: "WardLevelVisualizations", start_y: float) -> float:
        """Generate ward-level visualizations section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Ward-Level Visualizations", y)
        
        # Note: Map embedding will be implemented here
        # For now, just show map titles and paths
        
        maps = [
            ("Rainfall Distribution", visualizations.rainfall_map),
            ("Temperature Distribution", visualizations.temperature_map),
            ("Wind Speed Distribution", visualizations.wind_speed_map),
        ]
        
        for map_title, map_info in maps:
            y -= 0.5 * cm
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
            canvas.setFillColor(Colors.PRIMARY)
            canvas.drawString(self.margin_left, y, map_title)
            y -= 0.2 * cm
            
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.TEXT_SECONDARY)
            info_text = f"Resolution: {map_info.resolution} | Projection: {map_info.projection}"
            canvas.drawString(self.margin_left, y, info_text)
            y -= Fonts.BODY_SIZE * 1.5
            
            # TODO: Embed map image here
            # canvas.drawImage(map_info.image_path, ...)
            y -= 10 * cm  # Placeholder space for map
        
        return y


class ExtremeValuesGenerator(BaseSectionGenerator):
    """Generator for extreme values section."""
    
    def generate(self, canvas: "canvas.Canvas", extremes: "ExtremeValues", start_y: float) -> float:
        """Generate extreme values section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Extreme Values and Highlights", y)
        
        # Extreme events
        events = extremes.extreme_events
        event_texts = [
            f"Highest Single Day Rainfall: {events.highest_single_day_rainfall.ward_name} - "
            f"{format_rainfall(events.highest_single_day_rainfall.value)} on {format_date(events.highest_single_day_rainfall.date)}",
            f"Highest Weekly Rainfall: {events.highest_weekly_rainfall.ward_name} - "
            f"{format_rainfall(events.highest_weekly_rainfall.total)}",
            f"Hottest Day: {events.hottest_day.ward_name} - "
            f"{format_temperature(events.hottest_day.temperature)} on {format_date(events.hottest_day.date)}",
            f"Coolest Night: {events.coolest_night.ward_name} - "
            f"{format_temperature(events.coolest_night.temperature)} on {format_date(events.coolest_night.date)}",
            f"Strongest Wind Gust: {events.strongest_wind_gust.ward_name} - "
            f"{format_wind_speed(events.strongest_wind_gust.speed)} on {format_date(events.strongest_wind_gust.date)}",
        ]
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        for text in event_texts:
            lines = split_text_into_lines(text, self.content_width, Fonts.BODY_SIZE)
            for line in lines:
                canvas.drawString(self.margin_left, y, line)
                y -= Fonts.BODY_SIZE * 1.2
            y -= 0.2 * cm
        
        # Risk indicators
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Risk Indicators")
        y -= 0.3 * cm
        
        # Flood risk wards
        if extremes.risk_indicators.flood_risk_wards:
            canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
            canvas.setFillColor(Colors.TEXT_PRIMARY)
            canvas.drawString(self.margin_left, y, "Flood Risk Wards:")
            y -= Fonts.BODY_SIZE * 1.2
            
            for ward in extremes.risk_indicators.flood_risk_wards:
                risk_color = get_risk_level_color(ward.risk_level)
                canvas.setFillColor(risk_color)
                text = f"  • {ward.ward_name} ({ward.risk_level.upper()}): {ward.reason}"
                lines = split_text_into_lines(text, self.content_width, Fonts.BODY_SIZE)
                for line in lines:
                    canvas.drawString(self.margin_left, y, line)
                    y -= Fonts.BODY_SIZE * 1.2
        
        return y


class ImpactsAdvisoriesGenerator(BaseSectionGenerator):
    """Generator for impacts and advisories section."""
    
    def generate(self, canvas: "canvas.Canvas", impacts: "ImpactsAndAdvisories", start_y: float) -> float:
        """Generate impacts and advisories section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Impacts and Advisories", y)
        
        # Agricultural advisories
        y -= 0.3 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Agricultural Advisories")
        y -= 0.2 * cm
        
        ag = impacts.agricultural_advisories
        y = self._draw_paragraph(canvas, f"Rainfall Impact: {ag.rainfall_impact}", y)
        y = self._draw_paragraph(canvas, f"Temperature Effects: {ag.temperature_effects}", y)
        y = self._draw_paragraph(canvas, f"Optimal Timing: {ag.optimal_timing}", y)
        
        # General public advisories
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "General Public Advisories")
        y -= 0.2 * cm
        
        public = impacts.general_public_advisories
        y = self._draw_paragraph(canvas, f"Travel Conditions: {public.travel_conditions}", y)
        y = self._draw_paragraph(canvas, f"Outdoor Activities: {public.outdoor_activity_recommendations}", y)
        y = self._draw_paragraph(canvas, f"Safety Precautions: {public.safety_precautions}", y)
        
        return y


class DataSourcesMethodologyGenerator(BaseSectionGenerator):
    """Generator for data sources and methodology section."""
    
    def generate(self, canvas: "canvas.Canvas", methodology: "DataSourcesAndMethodology", start_y: float) -> float:
        """Generate data sources and methodology section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Data Sources and Methodology", y)
        
        # Forecast model
        model = methodology.forecast_model
        model_text = (
            f"Forecast Model: {model.name} {model.version} | "
            f"Grid Resolution: {model.grid_resolution} | "
            f"Forecast Horizon: {model.forecast_horizon} days"
        )
        
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        canvas.drawString(self.margin_left, y, model_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        # Data processing
        processing = methodology.data_processing
        processing_text = (
            f"Aggregation Method: {processing.aggregation_method} | "
            f"Grid Points: {processing.number_of_grid_points}"
        )
        canvas.drawString(self.margin_left, y, processing_text)
        y -= Fonts.BODY_SIZE * 1.5
        
        # Limitations
        y -= 0.5 * cm
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.H4_SIZE)
        canvas.setFillColor(Colors.PRIMARY)
        canvas.drawString(self.margin_left, y, "Limitations and Uncertainties")
        y -= 0.2 * cm
        
        limitations = methodology.limitations_and_uncertainties
        y = self._draw_paragraph(canvas, limitations.model_uncertainty, y)
        y = self._draw_paragraph(canvas, limitations.spatial_aggregation_limitations, y)
        
        return y


class MetadataDisclaimersGenerator(BaseSectionGenerator):
    """Generator for metadata and disclaimers section."""
    
    def generate(self, canvas: "canvas.Canvas", metadata: "MetadataAndDisclaimers", start_y: float) -> float:
        """Generate metadata and disclaimers section."""
        y = start_y
        
        # Section title
        y = self._draw_section_title(canvas, "Metadata and Disclaimers", y)
        
        # Disclaimer
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.BODY_SIZE)
        canvas.setFillColor(Colors.TEXT_PRIMARY)
        y = self._draw_paragraph(canvas, metadata.disclaimer_statement, y)
        
        # Copyright
        y -= 0.5 * cm
        copyright_info = metadata.copyright_and_attribution
        copyright_text = (
            f"Data Source: {copyright_info.data_source_attribution} | "
            f"System: {copyright_info.system_attribution}"
        )
        canvas.setFont(Fonts.FAMILY_SANS, Fonts.SMALL_SIZE)
        canvas.setFillColor(Colors.TEXT_SECONDARY)
        canvas.drawString(self.margin_left, y, copyright_text)
        y -= Fonts.SMALL_SIZE * 1.5
        
        # Contact information
        contact = metadata.contact_information
        if contact.technical_support:
            support_text = f"Technical Support: {contact.technical_support.get('contact', 'N/A')}"
            canvas.drawString(self.margin_left, y, support_text)
            y -= Fonts.SMALL_SIZE * 1.3
        
        return y
