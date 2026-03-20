#!/usr/bin/env python3
"""
Download Bas Milius weather icons required by WEATHER_ICON_KEYWORDS,
convert them from SVG to PNG for PDF generator, fixed paths and filenames.
"""

import os
import requests
import cairosvg

DEST_FOLDER = "backend/scripts/pdf_generator/assets/weather_icons"

# Correct mapping: desired PNG filename -> repo filename
ICON_SOURCES = {
    "clear-day.png": "clear-day",
    "partly-cloudy-day.png": "partly-cloudy-day",
    "mostly-cloudy.png": "cloudy",
    "cloudy.png": "cloudy",
    "drizzle.png": "drizzle",
    "rain.png": "rain",
    "showers.png": "showers",       # actual repo filename
    "thunderstorm.png": "thunderstorms",  # actual repo filename
    "fog.png": "fog",
    "wind.png": "wind",
}

BASE_URL = "https://raw.githubusercontent.com/basmilius/weather-icons/dev/production/fill/svg"

os.makedirs(DEST_FOLDER, exist_ok=True)

print("Downloading and converting weather icons to PNG...\n")

for png_filename, repo_name in ICON_SOURCES.items():
    url = f"{BASE_URL}/{repo_name}.svg"
    temp_svg_path = os.path.join(DEST_FOLDER, f"temp_{repo_name}.svg")
    png_path = os.path.join(DEST_FOLDER, png_filename)

    try:
        # Download SVG into temp file in the same folder
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(temp_svg_path, "wb") as f:
            f.write(r.content)

        # Convert SVG -> PNG
        cairosvg.svg2png(url=temp_svg_path, write_to=png_path, output_width=128, output_height=128)

        # Remove temp SVG
        os.remove(temp_svg_path)

        print(f"✓ {png_filename} ready")

    except Exception as e:
        print(f"✗ Failed {png_filename}: {e}")

print("\nAll icons downloaded and converted to PNG.")
print(f"Icons saved to: {DEST_FOLDER}")
