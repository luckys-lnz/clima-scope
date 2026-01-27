"""
Pydantic Models for PDF Report Generation

These models match the TypeScript interfaces defined in lib/report-structure.ts
and lib/weather-schemas.ts
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Cover Page Models
# ============================================================================

class ReportPeriod(BaseModel):
    """Report period information."""
    week_number: int
    year: int
    start_date: str = Field(..., description="ISO date format")
    end_date: str = Field(..., description="ISO date format")
    formatted: str = Field(..., description="Formatted string like 'Week 50, 2024 (December 2 - December 8, 2024)'")


class CountyInfo(BaseModel):
    """County information."""
    name: str
    code: str = Field(..., description="KNBS code")
    region: Optional[str] = None


class GenerationMetadata(BaseModel):
    """Report generation metadata."""
    generated_at: str = Field(..., description="ISO timestamp")
    model_run_timestamp: str = Field(..., description="ISO timestamp")
    data_source: str = Field(..., description="e.g., 'GFS v15.1'")
    system_version: str


class CoverPageInfo(BaseModel):
    """Cover page information."""
    report_title: str = Field(..., description="e.g., 'Weekly Weather Outlook for [County Name] County'")
    report_period: ReportPeriod
    county: CountyInfo
    generation_metadata: GenerationMetadata
    disclaimer: str


# ============================================================================
# Executive Summary Models
# ============================================================================

class TemperatureRange(BaseModel):
    """Temperature range."""
    min: float = Field(..., description="°C")
    max: float = Field(..., description="°C")


class SummaryStatistics(BaseModel):
    """Summary statistics for executive summary."""
    total_rainfall: float = Field(..., description="mm")
    mean_temperature: float = Field(..., description="°C")
    temperature_range: TemperatureRange
    max_wind_speed: float = Field(..., description="km/h")
    dominant_wind_direction: str


class ExecutiveSummary(BaseModel):
    """Executive summary section."""
    summary_statistics: SummaryStatistics
    key_highlights: List[str] = Field(..., description="3-5 bullet points")
    weather_pattern_summary: str = Field(..., description="3-4 sentence paragraph")


# ============================================================================
# Weekly Narrative Models
# ============================================================================

class TemporalBreakdown(BaseModel):
    """Temporal breakdown of the week."""
    early_week: str = Field(..., description="Days 1-2")
    mid_week: str = Field(..., description="Days 3-4")
    late_week: str = Field(..., description="Days 5-7")


class VariableSpecificDetails(BaseModel):
    """Variable-specific narrative details."""
    rainfall: str
    temperature: str
    wind: str
    humidity: Optional[str] = None


class WeeklyNarrative(BaseModel):
    """Weekly narrative summary section."""
    opening_paragraph: str
    temporal_breakdown: TemporalBreakdown
    variable_specific_details: VariableSpecificDetails
    spatial_variations: str


# ============================================================================
# Rainfall Outlook Models
# ============================================================================

class DailyRainfall(BaseModel):
    """Daily rainfall data."""
    day: str
    date: str
    rainfall: float = Field(..., description="mm")


class CountyRainfallSummary(BaseModel):
    """County-level rainfall summary."""
    total_weekly_rainfall: float = Field(..., description="mm")
    daily_breakdown: List[DailyRainfall]
    max_daily_intensity: float = Field(..., description="mm")
    number_of_rainy_days: int
    probability_above_normal: Optional[float] = Field(None, description="percentage")


class WardRainfallAnalysis(BaseModel):
    """Ward-level rainfall analysis."""
    ward_id: str
    ward_name: str
    total_rainfall: float = Field(..., description="mm")
    number_of_rainy_days: int
    peak_intensity_day: str


class TopWardByRainfall(BaseModel):
    """Top ward by rainfall."""
    ward_id: str
    ward_name: str
    total_rainfall: float


class ColorScaleItem(BaseModel):
    """Color scale item for maps."""
    range: str = Field(..., description="e.g., '0-20mm'")
    color: str


class RainfallDistributionMap(BaseModel):
    """Rainfall distribution map information."""
    image_path: str
    color_scale: List[ColorScaleItem]


class DailyChartData(BaseModel):
    """Daily chart data."""
    day: str
    rainfall: float


class DailyChart(BaseModel):
    """Daily chart structure."""
    data: List[DailyChartData]


class DryPeriod(BaseModel):
    """Dry period information."""
    start: str
    end: str


class TemporalPatterns(BaseModel):
    """Temporal patterns for rainfall."""
    daily_chart: DailyChart
    peak_rainfall_days: List[str]
    dry_periods: List[DryPeriod]


class RainfallOutlook(BaseModel):
    """Rainfall outlook section."""
    county_level_summary: CountyRainfallSummary
    ward_level_analysis: List[WardRainfallAnalysis]
    top_wards_by_rainfall: List[TopWardByRainfall]
    flood_risk_wards: List[str] = Field(..., description="ward IDs")
    rainfall_distribution_map: RainfallDistributionMap
    temporal_patterns: TemporalPatterns
    narrative_description: str = Field(..., description="2-3 paragraphs")


# ============================================================================
# Temperature Outlook Models
# ============================================================================

class TemperatureExtreme(BaseModel):
    """Temperature extreme value."""
    value: float = Field(..., description="°C")
    day: str


class DailyMeanTemperature(BaseModel):
    """Daily mean temperature."""
    day: str
    mean: float = Field(..., description="°C")


class CountyTemperatureSummary(BaseModel):
    """County-level temperature summary."""
    mean_weekly_temperature: float = Field(..., description="°C")
    maximum_temperature: TemperatureExtreme
    minimum_temperature: TemperatureExtreme
    temperature_range: float = Field(..., description="max - min")
    daily_mean_temperatures: List[DailyMeanTemperature]


class WardTemperatureAnalysis(BaseModel):
    """Ward-level temperature analysis."""
    ward_id: str
    ward_name: str
    mean_temperature: float = Field(..., description="°C")
    max_temperature: float = Field(..., description="°C")
    min_temperature: float = Field(..., description="°C")


class WardTemperature(BaseModel):
    """Ward temperature information."""
    ward_id: str
    ward_name: str
    temperature: float


class TemperatureDistributionMap(BaseModel):
    """Temperature distribution map information."""
    image_path: str
    color_scale: List[ColorScaleItem]


class DaytimeHigh(BaseModel):
    """Daytime high temperature."""
    day: str
    high: float = Field(..., description="°C")


class NighttimeLow(BaseModel):
    """Nighttime low temperature."""
    day: str
    low: float = Field(..., description="°C")


class DiurnalPatterns(BaseModel):
    """Diurnal temperature patterns."""
    daytime_highs: List[DaytimeHigh]
    nighttime_lows: List[NighttimeLow]


class TemperatureOutlook(BaseModel):
    """Temperature outlook section."""
    county_level_summary: CountyTemperatureSummary
    ward_level_analysis: List[WardTemperatureAnalysis]
    hottest_ward: WardTemperature
    coolest_ward: WardTemperature
    temperature_distribution_map: TemperatureDistributionMap
    diurnal_patterns: DiurnalPatterns
    narrative_description: str = Field(..., description="2-3 paragraphs")


# ============================================================================
# Wind Outlook Models
# ============================================================================

class WindExtreme(BaseModel):
    """Wind extreme value."""
    value: float = Field(..., description="km/h")
    day: str


class DailyPeakWind(BaseModel):
    """Daily peak wind speed."""
    day: str
    speed: float = Field(..., description="km/h")


class CountyWindSummary(BaseModel):
    """County-level wind summary."""
    mean_wind_speed: float = Field(..., description="km/h")
    maximum_gust: WindExtreme
    dominant_wind_direction: str
    daily_peak_wind_speeds: List[DailyPeakWind]


class WardWindAnalysis(BaseModel):
    """Ward-level wind analysis."""
    ward_id: str
    ward_name: str
    mean_wind_speed: float = Field(..., description="km/h")
    max_gust: float = Field(..., description="km/h")
    dominant_direction: str


class HighestWindWard(BaseModel):
    """Highest wind speed ward."""
    ward_id: str
    ward_name: str
    max_gust: float


class WindSpeedDistributionMap(BaseModel):
    """Wind speed distribution map information."""
    image_path: str
    color_scale: List[ColorScaleItem]


class WindRoseData(BaseModel):
    """Wind rose data."""
    direction: str
    frequency: float
    average_speed: float


class WindRose(BaseModel):
    """Wind rose information."""
    data: List[WindRoseData]


class DirectionFrequency(BaseModel):
    """Wind direction frequency."""
    direction: str
    frequency: float


class WindDirectionAnalysis(BaseModel):
    """Wind direction analysis."""
    wind_rose: Optional[WindRose] = None
    direction_frequency: List[DirectionFrequency]


class WindOutlook(BaseModel):
    """Wind outlook section."""
    county_level_summary: CountyWindSummary
    ward_level_analysis: List[WardWindAnalysis]
    highest_wind_speed_wards: List[HighestWindWard]
    wind_speed_distribution_map: WindSpeedDistributionMap
    wind_direction_analysis: Optional[WindDirectionAnalysis] = None
    narrative_description: str = Field(..., description="2-3 paragraphs")


# ============================================================================
# Ward-Level Visualizations Models
# ============================================================================

class MapInfo(BaseModel):
    """Map information."""
    image_path: str
    title: str
    resolution: str = Field(..., description="e.g., '300 DPI'")
    projection: str = Field(..., description="e.g., 'UTM Zone 37N, EPSG:32637'")


class WardLevelVisualizations(BaseModel):
    """Ward-level visualizations section."""
    rainfall_map: MapInfo
    temperature_map: MapInfo
    wind_speed_map: MapInfo


# ============================================================================
# Extreme Values Models
# ============================================================================

class ExtremeEvent(BaseModel):
    """Extreme weather event."""
    ward_id: str
    ward_name: str
    value: float
    date: Optional[str] = None


class ExtremeRainfall(BaseModel):
    """Extreme rainfall event."""
    ward_id: str
    ward_name: str
    value: float = Field(..., description="mm")
    date: str
    days: Optional[List[int]] = None


class ExtremeWeeklyRainfall(BaseModel):
    """Extreme weekly rainfall."""
    ward_id: str
    ward_name: str
    total: float = Field(..., description="mm")


class ExtremeTemperature(BaseModel):
    """Extreme temperature event."""
    ward_id: str
    ward_name: str
    temperature: float = Field(..., description="°C")
    date: str
    day: Optional[int] = None


class ExtremeWind(BaseModel):
    """Extreme wind event."""
    ward_id: str
    ward_name: str
    speed: float = Field(..., description="km/h")
    date: str


class ExtremeEvents(BaseModel):
    """Extreme weather events."""
    highest_single_day_rainfall: ExtremeRainfall
    highest_weekly_rainfall: ExtremeWeeklyRainfall
    hottest_day: ExtremeTemperature
    coolest_night: ExtremeTemperature
    strongest_wind_gust: ExtremeWind


class FloodRiskWard(BaseModel):
    """Flood risk ward information."""
    ward_id: str
    ward_name: str
    risk_level: Literal["low", "moderate", "high"]
    reason: str


class HeatStressWarning(BaseModel):
    """Heat stress warning."""
    ward_id: str
    ward_name: str
    warning_level: str


class WindAdvisory(BaseModel):
    """Wind advisory."""
    ward_id: str
    ward_name: str
    advisory_level: str


class RiskIndicators(BaseModel):
    """Risk indicators."""
    flood_risk_wards: List[FloodRiskWard]
    heat_stress_warnings: Optional[List[HeatStressWarning]] = None
    wind_advisories: Optional[List[WindAdvisory]] = None


class ExtremeValues(BaseModel):
    """Extreme values and highlights section."""
    extreme_events: ExtremeEvents
    risk_indicators: RiskIndicators
    notable_patterns: List[str]


# ============================================================================
# Impacts and Advisories Models
# ============================================================================

class AgriculturalAdvisories(BaseModel):
    """Agricultural advisories."""
    rainfall_impact: str
    temperature_effects: str
    optimal_timing: str


class WaterResources(BaseModel):
    """Water resources information."""
    rainfall_contribution: str
    reservoir_implications: Optional[str] = None


class HealthAdvisories(BaseModel):
    """Health advisories."""
    heat_related_warnings: Optional[List[str]] = None
    vector_borne_disease_risk: Optional[str] = None


class GeneralPublicAdvisories(BaseModel):
    """General public advisories."""
    travel_conditions: str
    outdoor_activity_recommendations: str
    safety_precautions: str


class SectorSpecificGuidance(BaseModel):
    """Sector-specific guidance."""
    energy: Optional[str] = None
    construction: Optional[str] = None
    tourism: Optional[str] = None


class ImpactsAndAdvisories(BaseModel):
    """Impacts and advisories section."""
    agricultural_advisories: AgriculturalAdvisories
    water_resources: WaterResources
    health_advisories: Optional[HealthAdvisories] = None
    general_public_advisories: GeneralPublicAdvisories
    sector_specific_guidance: SectorSpecificGuidance


# ============================================================================
# Data Sources and Methodology Models
# ============================================================================

class ForecastModel(BaseModel):
    """Forecast model information."""
    name: str = Field(..., description="e.g., 'GFS'")
    version: str = Field(..., description="e.g., 'v15.1'")
    run_date: str = Field(..., description="ISO timestamp")
    forecast_horizon: int = Field(..., description="days")
    grid_resolution: str = Field(..., description="e.g., '0.25°'")


class DataProcessing(BaseModel):
    """Data processing information."""
    aggregation_method: Literal["point-in-polygon", "area-weighted"]
    number_of_grid_points: int
    spatial_interpolation: str
    quality_control_measures: List[str]


class StationLocation(BaseModel):
    """Weather station location."""
    station_id: str
    name: str
    coordinates: dict = Field(..., description="{'lat': float, 'lon': float}")


class ObservationalData(BaseModel):
    """Observational data information."""
    source: str
    station_locations: List[StationLocation]
    integration_method: str
    last_update_timestamp: str


class BoundarySource(BaseModel):
    """Boundary data source."""
    source: str = Field(..., description="e.g., 'KNBS', 'HDX'")
    version: str
    date: str


class ShapefileSources(BaseModel):
    """Shapefile sources."""
    county_boundaries: BoundarySource
    ward_boundaries: BoundarySource
    coordinate_reference_system: str = Field(..., description="e.g., 'EPSG:4326' or 'EPSG:32637'")


class LimitationsAndUncertainties(BaseModel):
    """Limitations and uncertainties."""
    model_uncertainty: str
    spatial_aggregation_limitations: str
    temporal_resolution_constraints: str
    ward_level_forecast_accuracy: str


class DataSourcesAndMethodology(BaseModel):
    """Data sources and methodology section."""
    forecast_model: ForecastModel
    data_processing: DataProcessing
    observational_data: Optional[ObservationalData] = None
    shapefile_sources: ShapefileSources
    limitations_and_uncertainties: LimitationsAndUncertainties


# ============================================================================
# Metadata and Disclaimers Models
# ============================================================================

class GenerationMetadataDetailed(BaseModel):
    """Detailed generation metadata."""
    report_generation_timestamp: str = Field(..., description="ISO timestamp")
    system_version: str
    processing_duration: Optional[float] = Field(None, description="seconds")
    data_quality_flags: List[str]
    warnings: List[str]


class CopyrightAndAttribution(BaseModel):
    """Copyright and attribution."""
    data_source_attribution: str = Field(..., description="e.g., 'NOAA/NCEP for GFS'")
    system_attribution: str
    usage_rights: str


class MeteorologicalDepartment(BaseModel):
    """Meteorological department contact."""
    name: str
    contact: str


class ContactInformation(BaseModel):
    """Contact information."""
    meteorological_department: Optional[MeteorologicalDepartment] = None
    technical_support: dict = Field(..., description="{'contact': str}")
    report_feedback: dict = Field(..., description="{'mechanism': str}")


class MetadataAndDisclaimers(BaseModel):
    """Metadata and disclaimers section."""
    generation_metadata: GenerationMetadataDetailed
    disclaimer_statement: str
    copyright_and_attribution: CopyrightAndAttribution
    contact_information: ContactInformation


# ============================================================================
# Complete Report Model
# ============================================================================

class CompleteWeatherReport(BaseModel):
    """Complete weather report structure."""
    cover_page: CoverPageInfo
    executive_summary: ExecutiveSummary
    weekly_narrative: WeeklyNarrative
    rainfall_outlook: RainfallOutlook
    temperature_outlook: TemperatureOutlook
    wind_outlook: WindOutlook
    ward_level_visualizations: WardLevelVisualizations
    extreme_values: ExtremeValues
    impacts_and_advisories: ImpactsAndAdvisories
    data_sources_and_methodology: DataSourcesAndMethodology
    metadata_and_disclaimers: MetadataAndDisclaimers
    raw_data: dict = Field(..., description="CountyWeatherReport JSON data")


# ============================================================================
# Report Generation Config
# ============================================================================

class ReportGenerationConfig(BaseModel):
    """Report generation configuration."""
    include_observations: bool = False
    include_historical_comparison: bool = False
    include_extended_outlook: bool = False
    language: Literal["en", "sw"] = "en"
    page_size: Literal["A4", "Letter"] = "A4"
    map_resolution: int = 300  # DPI
    color_scheme: Literal["standard", "colorblind-friendly"] = "standard"
