# Sample County Weather Data

This directory contains comprehensive sample JSON files representing different climate zones in Kenya, all conforming to the official [County Weather Report JSON Schema](../../schemas/county-weather-report.schema.json).

## Available Samples

### 1. Nairobi (Highland Climate)
**File**: `nairobi_highland.json`
- **County ID**: 31
- **Climate**: Highland, temperate
- **Temperature**: 14.2°C - 26.8°C (mean: 21.5°C)
- **Rainfall**: 28.7mm (moderate)
- **Wards**: 5 (Westlands, Kasarani, Embakasi, Kibera, Langata)
- **Use Case**: Testing typical highland urban conditions

### 2. Mombasa (Coastal Climate)
**File**: `mombasa_coastal.json`
- **County ID**: 01
- **Climate**: Coastal, hot and humid
- **Temperature**: 24.1°C - 32.5°C (mean: 28.3°C)
- **Rainfall**: 15.3mm (low, dry season)
- **Wind**: Strong sea breezes (18.7 km/h mean, SE direction)
- **Wards**: 4 (Mvita, Likoni, Kisauni, Nyali)
- **Use Case**: Testing high temperature, low rainfall, strong winds

### 3. Turkana (Arid Climate)
**File**: `turkana_arid.json`
- **County ID**: 23
- **Climate**: Arid, extremely hot and dry
- **Temperature**: 22.3°C - 38.5°C (mean: 31.8°C) - **EXTREME HEAT**
- **Rainfall**: 1.2mm (very low, drought conditions)
- **Wind**: Strong winds (22.5 km/h mean, gusts up to 42.8 km/h)
- **Wards**: 4 (Turkana Central, North, South, Loima)
- **Use Case**: Testing edge cases for extreme heat, minimal rainfall, high winds

### 4. Nakuru (Rift Valley Climate)
**File**: `nakuru_rift.json`
- **County ID**: 32
- **Climate**: Rift Valley, cool and wet
- **Temperature**: 12.8°C - 24.5°C (mean: 19.8°C)
- **Rainfall**: 52.8mm (high rainfall week)
- **Wards**: 5 (Nakuru East/West, Gilgil, Naivasha, Molo)
- **Flood Risk**: Moderate in Molo (61.5mm), Low in Gilgil (58.2mm)
- **Use Case**: Testing high rainfall scenarios, flood risk detection

### 5. Kisumu (Western/Lake Climate)
**File**: `kisumu_western.json`
- **County ID**: 42
- **Climate**: Western Kenya, lake influence, high rainfall
- **Temperature**: 18.5°C - 29.8°C (mean: 25.2°C)
- **Rainfall**: 68.5mm (very high weekly total)
- **Wards**: 5 (Kisumu Central/East/West, Seme, Nyando)
- **Flood Risk**: **HIGH** in Nyando (74.5mm), Moderate in Kisumu East & Seme
- **Use Case**: Testing highest rainfall scenarios, multiple flood risk wards

## Climate Zone Coverage

These samples represent Kenya's diverse climate zones:

| Climate Zone | Representative County | Key Characteristics |
|--------------|----------------------|---------------------|
| Highland | Nairobi | Moderate temps, moderate rain |
| Coastal | Mombasa | Hot, humid, strong sea winds |
| Arid/Semi-arid | Turkana | Extreme heat, very low rainfall |
| Rift Valley | Nakuru | Cool, high rainfall, variable |
| Western/Lake | Kisumu | Warm, very high rainfall, flood-prone |

## Edge Cases Covered

These samples include various edge cases for testing:

1. **Temperature Extremes**:
   - Highest max: 38.5°C (Turkana)
   - Lowest min: 12.8°C (Nakuru)
   - Largest diurnal range: 16.2°C (Turkana)

2. **Rainfall Extremes**:
   - Highest weekly total: 68.5mm (Kisumu)
   - Lowest weekly total: 1.2mm (Turkana)
   - Highest single-day intensity: 22.3mm (Kisumu)

3. **Wind Extremes**:
   - Strongest gusts: 42.8 km/h (Turkana)
   - Varied wind directions: NE, SE, E, W
   - Coastal vs inland wind patterns

4. **Flood Risk Scenarios**:
   - No flood risk (Nairobi, Mombasa, Turkana)
   - Low-moderate risk (Nakuru: 2 wards)
   - High risk (Kisumu: 3 wards including one HIGH risk)

5. **Data Quality Scenarios**:
   - Excellent quality (Mombasa: 100% coverage, 0% missing)
   - Good quality with warnings (Turkana: sparse grid coverage)
   - Above-normal rainfall warnings (Nakuru, Kisumu)

## Schema Validation

All samples are validated against the JSON Schema. To validate:

```bash
# Validate all samples
python scripts/validate_schema.py --all

# Validate a single file
python scripts/validate_schema.py backend/resources/sample_data/nairobi_highland.json
```

### Validation Requirements

Each sample must include:

**Required fields**:
- `schema_version`: "1.0"
- `county_id`: 2-digit KNBS code
- `county_name`: Official county name
- `period`: {start, end, week_number, year}
- `variables`: {temperature, rainfall, wind} with weekly & daily breakdowns
- `metadata`: GFS run info, generation timestamp, grid details

**Optional but recommended**:
- `wards`: Array of ward-level summaries
- `extremes`: Highest/lowest values by ward
- `disclaimer`: Legal disclaimer
- `quality_flags`: Data quality indicators

## Usage in Development

### For Backend Testing

```python
import json
from pathlib import Path

# Load a sample
sample_path = Path("backend/resources/sample_data/nairobi_highland.json")
with open(sample_path) as f:
    weather_data = json.load(f)

# Use in tests
from backend.app.services import ReportGenerator

generator = ReportGenerator()
complete_report = generator.generate_complete_report(weather_data)
```

### For PDF Generation

```python
from pdf_generator import EnhancedPDFBuilder
from pdf_generator.section_generators import generate_all_sections

# Generate PDF from sample
sections = generate_all_sections(weather_data)
builder = EnhancedPDFBuilder()
pdf_path = builder.build("test_report.pdf", sections)
```

### For Frontend Development

```typescript
// Mock API responses in development
import nairobiSample from '@/backend/resources/sample_data/nairobi_highland.json';

// Use as fixture in tests
expect(weatherData).toMatchSchema(nairobiSample);
```

## Adding New Samples

To add a new sample county:

1. **Copy an existing sample** closest to your target climate zone
2. **Update county information**:
   - County ID (KNBS 2-digit code)
   - County name
   - Period dates
3. **Adjust weather variables** to match expected climate:
   - Temperature ranges (check historical data)
   - Rainfall patterns (consider season)
   - Wind patterns (consider geography)
4. **Update ward-level data**:
   - Use actual ward names and IDs
   - Adjust ward-level values realistically
5. **Set appropriate metadata**:
   - Grid points used (based on county size)
   - Quality flags and warnings
6. **Validate**:
   ```bash
   python scripts/validate_schema.py backend/resources/sample_data/your_new_sample.json
   ```

## Data Sources

These samples are **synthetic** but based on:
- Historical GFS forecast patterns
- Kenya Meteorological Department climate data
- KNBS county and ward administrative boundaries
- Typical seasonal weather patterns (January reference period)

**Note**: These are NOT real forecasts. Use only for development and testing.

## Maintenance

- **Update samples** when schema changes (currently v1.0)
- **Add seasonal variations** as needed (rainy season vs dry season)
- **Test edge cases** for AI narrative generation quality
- **Validate regularly** to ensure schema compliance

## Questions?

See:
- [County Weather Report JSON Schema](../../schemas/county-weather-report.schema.json)
- [Schema Validation Script](../../scripts/validate_schema.py)
- [Master Implementation Plan](../../.cursor/plans/master_implementation_plan.md)
