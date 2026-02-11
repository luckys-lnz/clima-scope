"""
Main PDF Builder for Clima-scope Reports

Orchestrates the generation of all 11 report sections into a complete PDF.
"""

import os
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from .models import CompleteWeatherReport
from .config import ReportConfig, Colors, Fonts, Spacing
from .section_generators import (
    CoverPageGenerator,
    ExecutiveSummaryGenerator,
    WeeklyNarrativeGenerator,
    RainfallOutlookGenerator,
    TemperatureOutlookGenerator,
    WindOutlookGenerator,
    WardVisualizationsGenerator,
    ExtremeValuesGenerator,
    ImpactsAdvisoriesGenerator,
    DataSourcesMethodologyGenerator,
    MetadataDisclaimersGenerator,
)


class PDFReportBuilder:
    """Main class for building PDF reports."""
    
    def __init__(self, report_data: dict, config: Optional[ReportConfig] = None):
        """
        Initialize PDF builder.
        
        Args:
            report_data: Dictionary matching CompleteWeatherReport structure
            config: Optional report configuration
        """
        # Validate and parse report data
        self.report = CompleteWeatherReport(**report_data)
        self.config = config or ReportConfig()
        
        # Initialize section generators
        self._init_generators()
        
        # PDF canvas (will be created in generate method)
        self.canvas = None
        self.current_y = 0
        
    def _init_generators(self):
        """Initialize all section generators."""
        self.cover_page_gen = CoverPageGenerator(self.config)
        self.exec_summary_gen = ExecutiveSummaryGenerator(self.config)
        self.narrative_gen = WeeklyNarrativeGenerator(self.config)
        self.rainfall_gen = RainfallOutlookGenerator(self.config)
        self.temperature_gen = TemperatureOutlookGenerator(self.config)
        self.wind_gen = WindOutlookGenerator(self.config)
        self.ward_viz_gen = WardVisualizationsGenerator(self.config)
        self.extremes_gen = ExtremeValuesGenerator(self.config)
        self.impacts_gen = ImpactsAdvisoriesGenerator(self.config)
        self.methodology_gen = DataSourcesMethodologyGenerator(self.config)
        self.metadata_gen = MetadataDisclaimersGenerator(self.config)
    
    def generate(self, output_path: str) -> str:
        """
        Generate complete PDF report.
        
        Args:
            output_path: Path where PDF will be saved
        
        Returns:
            Path to generated PDF file
        """
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create PDF canvas
        self.canvas = canvas.Canvas(
            output_path,
            pagesize=self.config.page_dimensions
        )
        
        # Set initial position
        self.current_y = self.config.page_height - (self.config.margin_top * cm)
        
        # Generate all sections in order
        self._generate_cover_page()
        self.canvas.showPage()  # New page after cover
        
        self._generate_executive_summary()
        self._add_page_break_if_needed()
        
        self._generate_weekly_narrative()
        self._add_page_break_if_needed()
        
        self._generate_rainfall_outlook()
        self._add_page_break_if_needed()
        
        self._generate_temperature_outlook()
        self._add_page_break_if_needed()
        
        self._generate_wind_outlook()
        self._add_page_break_if_needed()
        
        self._generate_ward_visualizations()
        self._add_page_break_if_needed()
        
        self._generate_extreme_values()
        self._add_page_break_if_needed()
        
        self._generate_impacts_advisories()
        self._add_page_break_if_needed()
        
        self._generate_data_sources_methodology()
        self._add_page_break_if_needed()
        
        self._generate_metadata_disclaimers()
        
        # Save PDF
        self.canvas.save()
        
        return output_path
    
    def _generate_cover_page(self):
        """Generate cover page section."""
        self.current_y = self.cover_page_gen.generate(
            self.canvas,
            self.report.cover_page,
            self.current_y
        )
    
    def _generate_executive_summary(self):
        """Generate executive summary section."""
        self.current_y = self.exec_summary_gen.generate(
            self.canvas,
            self.report.executive_summary,
            self.current_y
        )
    
    def _generate_weekly_narrative(self):
        """Generate weekly narrative section."""
        self.current_y = self.narrative_gen.generate(
            self.canvas,
            self.report.weekly_narrative,
            self.current_y
        )
    
    def _generate_rainfall_outlook(self):
        """Generate rainfall outlook section."""
        self.current_y = self.rainfall_gen.generate(
            self.canvas,
            self.report.rainfall_outlook,
            self.current_y
        )
    
    def _generate_temperature_outlook(self):
        """Generate temperature outlook section."""
        self.current_y = self.temperature_gen.generate(
            self.canvas,
            self.report.temperature_outlook,
            self.current_y
        )
    
    def _generate_wind_outlook(self):
        """Generate wind outlook section."""
        self.current_y = self.wind_gen.generate(
            self.canvas,
            self.report.wind_outlook,
            self.current_y
        )
    
    def _generate_ward_visualizations(self):
        """Generate ward-level visualizations section."""
        self.current_y = self.ward_viz_gen.generate(
            self.canvas,
            self.report.ward_level_visualizations,
            self.current_y
        )
    
    def _generate_extreme_values(self):
        """Generate extreme values section."""
        self.current_y = self.extremes_gen.generate(
            self.canvas,
            self.report.extreme_values,
            self.current_y
        )
    
    def _generate_impacts_advisories(self):
        """Generate impacts and advisories section."""
        self.current_y = self.impacts_gen.generate(
            self.canvas,
            self.report.impacts_and_advisories,
            self.current_y
        )
    
    def _generate_data_sources_methodology(self):
        """Generate data sources and methodology section."""
        self.current_y = self.methodology_gen.generate(
            self.canvas,
            self.report.data_sources_and_methodology,
            self.current_y
        )
    
    def _generate_metadata_disclaimers(self):
        """Generate metadata and disclaimers section."""
        self.current_y = self.metadata_gen.generate(
            self.canvas,
            self.report.metadata_and_disclaimers,
            self.current_y
        )
    
    def _add_page_break_if_needed(self, min_space: float = 2.0):
        """
        Add a new page if there's not enough space for the next section.
        
        Args:
            min_space: Minimum space needed in cm
        """
        min_space_points = min_space * cm
        if self.current_y < (self.config.margin_bottom * cm + min_space_points):
            self.canvas.showPage()
            self.current_y = self.config.page_height - (self.config.margin_top * cm)
    
    def _draw_header_footer(self, page_num: int, total_pages: int):
        """
        Draw header and footer on each page (except cover).
        
        Args:
            page_num: Current page number
            total_pages: Total number of pages
        """
        # Header
        header_y = self.config.page_height - (0.5 * cm)
        self.canvas.setFont(Fonts.FAMILY_SANS, Fonts.SMALL_SIZE)
        self.canvas.setFillColor(Colors.TEXT_SECONDARY)
        
        county_name = self.report.cover_page.county.name
        header_text = f"Weekly Weather Outlook - {county_name} County"
        self.canvas.drawString(
            self.config.margin_left * cm,
            header_y,
            header_text
        )
        
        # Footer
        footer_y = 1.0 * cm
        footer_text = f"Page {page_num} of {total_pages}"
        text_width = self.canvas.stringWidth(footer_text, Fonts.FAMILY_SANS, Fonts.SMALL_SIZE)
        self.canvas.drawString(
            (self.config.page_width - self.config.margin_right * cm - text_width),
            footer_y,
            footer_text
        )
        
        # Draw line separator
        self.canvas.setStrokeColor(Colors.TEXT_LIGHT)
        self.canvas.setLineWidth(0.5)
        # Header line
        self.canvas.line(
            self.config.margin_left * cm,
            header_y - 0.2 * cm,
            self.config.page_width - self.config.margin_right * cm,
            header_y - 0.2 * cm
        )
        # Footer line
        self.canvas.line(
            self.config.margin_left * cm,
            footer_y + 0.5 * cm,
            self.config.page_width - self.config.margin_right * cm,
            footer_y + 0.5 * cm
        )


if __name__ == "__main__":
    print("="*70)
    print("ERROR: This module should not be run directly")
    print("="*70)
    print("\nThis is a library module. To generate PDFs, use one of these methods:\n")
    print("1. Using the sample generation script:")
    print("   cd pdf_generator")
    print("   python generate_sample.py")
    print()
    print("2. Using the AI-powered generation script:")
    print("   cd pdf_generator")
    print("   python generate_ai_sample.py")
    print()
    print("3. As a Python module:")
    print("   python -m pdf_generator.generate_sample")
    print("   python -m pdf_generator.generate_ai_sample")
    print()
    print("4. In your own code:")
    print("   from pdf_generator import PDFReportBuilder")
    print("   builder = PDFReportBuilder(report_data)")
    print("   builder.generate('output.pdf')")
    print()
    print("See pdf_generator/README.md for more details.")
    print("="*70)
    import sys
    sys.exit(1)
