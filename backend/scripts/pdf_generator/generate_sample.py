"""
Sample PDF Generation Script

Generates a sample PDF report from the Nairobi sample data.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_generator.pdf_builder import PDFReportBuilder
from pdf_generator.config import ReportConfig


def main():
    """Generate sample PDF report."""
    # Load sample data
    sample_data_path = Path(__file__).parent / "sample_data" / "nairobi_sample.json"
    
    if not sample_data_path.exists():
        print(f"Error: Sample data file not found at {sample_data_path}")
        return 1
    
    with open(sample_data_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate PDF
    output_path = output_dir / "nairobi_report_sample.pdf"
    
    print(f"Generating PDF report...")
    print(f"Input: {sample_data_path}")
    print(f"Output: {output_path}")
    
    try:
        config = ReportConfig(
            page_size="A4",
            language="en"
        )
        
        builder = PDFReportBuilder(report_data, config=config)
        generated_path = builder.generate(str(output_path))
        
        print(f"\n[SUCCESS] PDF generated successfully!")
        print(f"   Location: {generated_path}")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
