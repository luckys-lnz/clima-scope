#!/usr/bin/env python3
"""
Create Mock Map Images

Creates placeholder map images for testing PDF generation and map embedding
before Person A's geospatial processing pipeline is complete.

These mocks match the expected format:
- PNG format
- 1200x900 pixels
- 300 DPI
- Labeled with county and variable names
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys


def create_mock_map(
    county_id: str,
    county_name: str,
    variable: str,
    output_path: Path,
    width: int = 1200,
    height: int = 900,
    dpi: int = 300
):
    """
    Create a mock weather map image.
    
    Args:
        county_id: KNBS county code
        county_name: County name
        variable: Weather variable (rainfall, temperature, wind)
        output_path: Where to save the image
        width: Image width in pixels
        height: Image height in pixels
        dpi: DPI resolution
    """
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Color scheme based on variable
    colors = {
        'rainfall': ('#3b82f6', '#dbeafe'),  # Blue
        'temperature': ('#ef4444', '#fee2e2'),  # Red
        'wind': ('#10b981', '#d1fae5')  # Green
    }
    primary_color, bg_color = colors.get(variable, ('#6b7280', '#f3f4f6'))
    
    # Draw colored background
    draw.rectangle([50, 50, width-50, height-50], fill=bg_color, outline=primary_color, width=3)
    
    # Try to use a nicer font, fall back to default
    try:
        # Try common font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        font_large = None
        font_medium = None
        for font_path in font_paths:
            if Path(font_path).exists():
                font_large = ImageFont.truetype(font_path, 72)
                font_medium = ImageFont.truetype(font_path, 36)
                break
        
        if not font_large:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Draw text
    title_text = f"{county_name} County"
    subtitle_text = f"{variable.upper()} MAP"
    label_text = "Mock Placeholder"
    info_text = f"{width}x{height}px @ {dpi} DPI"
    
    # Calculate positions (center align)
    title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) / 2
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_medium)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) / 2
    
    # Draw text elements
    draw.text((title_x, height/2 - 100), title_text, fill=primary_color, font=font_large)
    draw.text((subtitle_x, height/2), subtitle_text, fill=primary_color, font=font_medium)
    
    # Draw info at bottom
    draw.text((100, height - 150), label_text, fill='#6b7280', font=font_medium)
    draw.text((100, height - 100), info_text, fill='#9ca3af', font=font_medium)
    draw.text((100, height - 60), f"County ID: {county_id}", fill='#9ca3af', font=font_medium)
    
    # Draw legend box
    legend_x = width - 350
    legend_y = 100
    draw.rectangle([legend_x, legend_y, legend_x + 300, legend_y + 200], fill='white', outline=primary_color, width=2)
    draw.text((legend_x + 20, legend_y + 20), "LEGEND", fill=primary_color, font=font_medium)
    draw.text((legend_x + 20, legend_y + 70), "Color scale", fill='#6b7280')
    draw.text((legend_x + 20, legend_y + 100), "will appear here", fill='#6b7280')
    draw.text((legend_x + 20, legend_y + 130), "when Person A", fill='#6b7280')
    draw.text((legend_x + 20, legend_y + 160), "generates map", fill='#6b7280')
    
    # Save with DPI info
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, dpi=(dpi, dpi))
    print(f"Created mock map: {output_path}")


def main():
    """Create mock maps for sample counties."""
    # Base directory for mock maps
    base_dir = Path(__file__).parent.parent.parent / "data" / "maps" / "mock"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample counties to create mocks for
    counties = [
        ("31", "Nairobi"),
        ("01", "Mombasa"),
        ("23", "Turkana"),
        ("32", "Nakuru"),
        ("42", "Kisumu")
    ]
    
    variables = ["rainfall", "temperature", "wind"]
    
    print("Creating mock map images...")
    print(f"Output directory: {base_dir}")
    print()
    
    for county_id, county_name in counties:
        for variable in variables:
            output_file = base_dir / f"{county_id}_{variable}_mock.png"
            create_mock_map(
                county_id=county_id,
                county_name=county_name,
                variable=variable,
                output_path=output_file
            )
    
    print()
    print(f"✓ Created {len(counties) * len(variables)} mock map images")
    print()
    print("These mocks can be used for:")
    print("  - Testing PDF generation with map embedding")
    print("  - UI development and frontend integration")
    print("  - API testing for map upload/download endpoints")
    print()
    print("To use in tests:")
    print(f"  map_path = Path('{base_dir}/31_rainfall_mock.png')")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("ERROR: PIL (Pillow) not installed.")
        print("Install with: pip install Pillow")
        print()
        print(f"Error details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
