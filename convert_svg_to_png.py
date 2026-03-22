import os
from pathlib import Path
import cairosvg

# Paths
svg_dir = Path("backend/app/utils/assets/weather_icons/svg")
png_dir = Path("backend/app/utils/assets/weather_icons/png")
png_dir.mkdir(exist_ok=True)  # Create output folder if it doesn't exist

# Convert each SVG to PNG
for svg_file in svg_dir.glob("*.svg"):
    png_file = png_dir / (svg_file.stem + ".png")
    cairosvg.svg2png(url=str(svg_file), write_to=str(png_file), output_width=32, output_height=32)
    print(f"Converted {svg_file.name} -> {png_file.name}")
