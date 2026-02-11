"""
Sample Script: AI-Powered Report Generation

This script demonstrates how to use the AI-powered report generator
to create professional weather reports from raw data.
"""

import json
import sys
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env file from: {env_path}")
except ImportError:
    pass  # python-dotenv not installed, use environment variables

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_generator.report_generator import ReportGenerator
from pdf_generator.ai_service import AIProvider
from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder
from pdf_generator.config import ReportConfig


def main():
    """Generate AI-powered PDF report."""
    
    # Check for API key
    import os
    api_key_openai = os.getenv("OPENAI_API_KEY")
    api_key_anthropic = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key_openai and not api_key_anthropic:
        print("ERROR: No API key found!")
        print("\nPlease set one of the following environment variables:")
        print("  - OPENAI_API_KEY (for OpenAI)")
        print("  - ANTHROPIC_API_KEY (for Anthropic)")
        print("\nSee API_KEY_SETUP.md for instructions.")
        return 1
    
    # Choose provider (default to OpenAI if both are set)
    provider = AIProvider.OPENAI if api_key_openai else AIProvider.ANTHROPIC
    print(f"Using AI provider: {provider.value}")
    
    # Check for demo mode (skip API calls if quota issues)
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # Load raw weather data
    # In a real scenario, this would come from your data processing pipeline
    # For this example, we'll use a simplified structure
    sample_data_path = Path(__file__).parent / "sample_data" / "nairobi_sample.json"
    
    if not sample_data_path.exists():
        print(f"Error: Sample data file not found at {sample_data_path}")
        print("Using minimal sample data structure...")
        
        # Create minimal sample data
        raw_data = {
            "county_id": "31",
            "county_name": "Nairobi",
            "period": {
                "start_date": "2026-01-19",
                "end_date": "2026-01-25",
                "week_number": 3,
                "year": 2026
            },
            "variables": {
                "rainfall": {
                    "weekly": {
                        "total": 45.2,
                        "max_intensity": 12.3,
                        "rainy_days": 6
                    },
                    "daily": [6.2, 8.5, 12.3, 10.7, 4.8, 2.1, 0.8],
                    "units": "mm"
                },
                "temperature": {
                    "weekly": {
                        "mean": 24.8,
                        "max": 28.3,
                        "min": 18.5
                    },
                    "daily": [26.1, 27.3, 28.2, 25.8, 24.1, 23.9, 22.7],
                    "daily_min": [19.1, 19.5, 20.2, 19.8, 18.5, 18.2, 18.1],
                    "units": "°C"
                },
                "wind": {
                    "weekly": {
                        "mean_speed": 12.5,
                        "max_gust": 25.4,
                        "dominant_direction": "NE"
                    },
                    "daily_peak": [15.2, 18.7, 22.1, 16.3, 14.8, 13.5, 12.9],
                    "units": "km/h"
                }
            },
            "wards": [
                {
                    "ward_id": "31001",
                    "ward_name": "Westlands",
                    "rainfall_total": 38.5,
                    "temp_max": 27.1,
                    "temp_min": 18.5,
                    "temp_mean": 22.8,
                    "wind_max": 28.3,
                    "wind_mean": 14.2
                },
                {
                    "ward_id": "31002",
                    "ward_name": "Kasarani",
                    "rainfall_total": 52.3,
                    "temp_max": 28.1,
                    "temp_min": 19.2,
                    "temp_mean": 23.6,
                    "wind_max": 26.5,
                    "wind_mean": 15.1
                }
            ],
            "extremes": {
                "highest_rainfall": {
                    "ward_id": "31002",
                    "ward_name": "Kasarani",
                    "value": 52.3
                },
                "hottest_ward": {
                    "ward_id": "31002",
                    "ward_name": "Kasarani",
                    "value": 28.1
                },
                "coolest_ward": {
                    "ward_id": "31001",
                    "ward_name": "Westlands",
                    "value": 18.5
                },
                "windiest_ward": {
                    "ward_id": "31001",
                    "ward_name": "Westlands",
                    "value": 28.3
                },
                "flood_risk_wards": []
            },
            "metadata": {
                "data_source": "GFS",
                "model_run": "2026-01-18T00:00:00Z",
                "generated": "2026-01-18T10:00:00Z",
                "aggregation_method": "point-in-polygon",
                "grid_resolution": "0.25°",
                "grid_points_used": 184,
                "system_version": "1.0.0"
            },
            "disclaimer": "This report is generated from automated weather forecast data. Ward-level maps are derived from spatial aggregation of global forecasts for planning purposes only. Contact the local meteorological office for official updates and warnings."
        }
    else:
        with open(sample_data_path, 'r', encoding='utf-8') as f:
            # If the sample is already a CompleteWeatherReport, extract raw_data
            sample_data = json.load(f)
            if "raw_data" in sample_data:
                raw_data = sample_data["raw_data"]
            else:
                # Assume it's raw CountyWeatherReport format
                raw_data = sample_data
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("AI-Powered Report Generation")
    print("="*60)
    print(f"\n1. Generating complete report from raw data...")
    print(f"   County: {raw_data.get('county_name', 'Unknown')}")
    
    try:
        # Initialize report generator
        generator = ReportGenerator(ai_provider=provider)
        
        # Generate complete report using AI
        complete_report = generator.generate_complete_report(raw_data)
        
        print(f"\n2. Report structure generated successfully!")
        print(f"   - Executive summary: ✓")
        print(f"   - Weekly narrative: ✓")
        print(f"   - Variable narratives: ✓")
        print(f"   - Impacts and advisories: ✓")
        
        # Save complete report JSON (optional, for debugging)
        json_output = output_dir / "complete_report.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(complete_report, f, indent=2, ensure_ascii=False)
        print(f"\n3. Complete report JSON saved to: {json_output}")
        
        # Generate PDF
        print(f"\n4. Generating enhanced PDF...")
        pdf_output = output_dir / "ai_generated_report.pdf"
        
        config = ReportConfig(
            page_size="A4",
            language="en"
        )
        
        pdf_builder = EnhancedPDFBuilder(complete_report, config=config)
        generated_path = pdf_builder.generate(str(pdf_output))
        
        print(f"\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nPDF generated: {generated_path}")
        print(f"JSON saved: {json_output}")
        print(f"\nThe report includes:")
        print(f"  - AI-generated executive summary")
        print(f"  - Professional narrative sections")
        print(f"  - Sector-specific advisories")
        print(f"  - Enhanced formatting with tables and proper layout")
        
        return 0
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n" + "="*60)
        print("ERROR")
        print("="*60)
        print(f"\nError generating report: {error_msg}")
        
        # Provide helpful error messages for common issues
        if "insufficient_quota" in error_msg.lower() or "exceeded your current quota" in error_msg.lower():
            print("\n" + "="*60)
            print("INSUFFICIENT QUOTA DETECTED")
            print("="*60)
            print("\nYour OpenAI API key is valid, but your account has insufficient credits.")
            print("\nTo fix this:")
            print("1. Add credits to your OpenAI account:")
            print("   https://platform.openai.com/account/billing")
            print("\n2. Check your usage limits:")
            print("   https://platform.openai.com/account/limits")
            print("\n3. Once credits are added, run this script again.")
            print("\nNote: The API key and code are working correctly!")
            print("      You just need to add billing credits to use the API.")
        elif "Invalid API key" in error_msg or "401" in error_msg or "invalid_api_key" in error_msg.lower():
            print("\nYour API key appears to be invalid.")
            print("Check your .env file and verify the key is correct.")
            print("Get a new key from: https://platform.openai.com/api-keys")
        elif "Rate limit" in error_msg or "429" in error_msg:
            print("\nRate limit exceeded. Wait a moment and try again.")
        else:
            print("\nFull error details:")
            import traceback
            traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
