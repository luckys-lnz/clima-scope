"""
AI-Powered Report Generator

Transforms raw CountyWeatherReport JSON into CompleteWeatherReport
using AI to generate narrative content.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .models import CompleteWeatherReport
from .ai_service import AIService, AIProvider


class ReportGenerator:
    """Generates complete weather reports from raw data using AI."""
    
    def __init__(
        self,
        ai_provider: AIProvider = AIProvider.OPENAI,
        api_key: Optional[str] = None
    ):
        """
        Initialize report generator.
        
        Args:
            ai_provider: AI provider to use
            api_key: Optional API key (reads from env if not provided)
        """
        self.ai_service = AIService(provider=ai_provider, api_key=api_key)
    
    def generate_complete_report(
        self,
        raw_report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete weather report from raw CountyWeatherReport data.
        
        Args:
            raw_report_data: Raw CountyWeatherReport JSON data
            
        Returns:
            CompleteWeatherReport dictionary ready for PDF generation
        """
        county_name = raw_report_data.get("county_name", "Unknown")
        
        # Generate AI-powered narrative sections
        print(f"Generating executive summary for {county_name}...")
        executive_summary = self.ai_service.generate_executive_summary(
            raw_report_data, county_name
        )
        
        print(f"Generating weekly narrative for {county_name}...")
        weekly_narrative = self.ai_service.generate_weekly_narrative(
            raw_report_data, county_name
        )
        
        # Generate variable-specific narratives
        variables = raw_report_data.get("variables", {})
        
        print(f"Generating rainfall narrative...")
        rainfall_narrative = self.ai_service.generate_rainfall_narrative(
            variables.get("rainfall", {}), county_name
        )
        
        print(f"Generating temperature narrative...")
        temperature_narrative = self.ai_service.generate_temperature_narrative(
            variables.get("temperature", {}), county_name
        )
        
        print(f"Generating wind narrative...")
        wind_narrative = self.ai_service.generate_wind_narrative(
            variables.get("wind", {}), county_name
        )
        
        print(f"Generating impacts and advisories...")
        impacts = self.ai_service.generate_impacts_advisories(
            raw_report_data, county_name
        )
        
        # Build complete report structure
        complete_report = self._build_report_structure(
            raw_report_data,
            executive_summary,
            weekly_narrative,
            rainfall_narrative,
            temperature_narrative,
            wind_narrative,
            impacts
        )
        
        return complete_report
    
    def _build_report_structure(
        self,
        raw_data: Dict[str, Any],
        executive_summary: Dict[str, Any],
        weekly_narrative: Dict[str, Any],
        rainfall_narrative: str,
        temperature_narrative: str,
        wind_narrative: str,
        impacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build complete report structure from components."""
        
        # Extract period information
        period = raw_data.get("period", {})
        week_num = period.get("week_number", 1)
        year = period.get("year", datetime.now().year)
        start_date = period.get("start_date", "")
        end_date = period.get("end_date", "")
        
        # Format period string
        period_formatted = self._format_period(week_num, year, start_date, end_date)
        
        # Extract metadata
        metadata = raw_data.get("metadata", {})
        variables = raw_data.get("variables", {})
        wards = raw_data.get("wards", [])
        extremes = raw_data.get("extremes", {})
        
        # Build cover page
        cover_page = {
            "report_title": f"Weekly Weather Outlook for {raw_data.get('county_name', 'Unknown')} County",
            "report_period": {
                "week_number": week_num,
                "year": year,
                "start_date": start_date,
                "end_date": end_date,
                "formatted": period_formatted
            },
            "county": {
                "name": raw_data.get("county_name", "Unknown"),
                "code": raw_data.get("county_id", ""),
                "region": None
            },
            "generation_metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "model_run_timestamp": metadata.get("model_run", ""),
                "data_source": metadata.get("data_source", "GFS"),
                "system_version": metadata.get("system_version", "1.0.0")
            },
            "disclaimer": raw_data.get("disclaimer", "This report is generated from automated weather forecast data. Ward-level maps are derived from spatial aggregation of global forecasts for planning purposes only. Contact the local meteorological office for official updates and warnings.")
        }
        
        # Build complete report (simplified - you'll need to expand this based on your full schema)
        complete_report = {
            "cover_page": cover_page,
            "executive_summary": executive_summary,
            "weekly_narrative": weekly_narrative,
            "rainfall_outlook": self._build_rainfall_outlook(variables.get("rainfall", {}), wards, rainfall_narrative),
            "temperature_outlook": self._build_temperature_outlook(variables.get("temperature", {}), wards, temperature_narrative),
            "wind_outlook": self._build_wind_outlook(variables.get("wind", {}), wards, wind_narrative),
            "ward_level_visualizations": self._build_ward_visualizations(),
            "extreme_values": self._build_extreme_values(extremes, wards),
            "impacts_and_advisories": impacts,
            "data_sources_and_methodology": self._build_methodology(metadata),
            "metadata_and_disclaimers": self._build_metadata_disclaimers(metadata),
            "raw_data": raw_data
        }
        
        return complete_report
    
    def _format_period(self, week_num: int, year: int, start: str, end: str) -> str:
        """Format period string."""
        from .utils import format_date
        start_formatted = format_date(start, "%B %d")
        end_formatted = format_date(end, "%B %d, %Y")
        return f"Week {week_num}, {year} ({start_formatted} - {end_formatted})"
    
    def _build_rainfall_outlook(self, rainfall_data: Dict, wards: list, narrative: str) -> Dict:
        """Build rainfall outlook section."""
        weekly = rainfall_data.get("weekly", {})
        daily = rainfall_data.get("daily", [])
        
        # Build daily breakdown
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_breakdown = []
        for i, amount in enumerate(daily[:7]):
            daily_breakdown.append({
                "day": days[i] if i < len(days) else f"Day {i+1}",
                "date": "",  # You'll need to calculate actual dates
                "rainfall": amount
            })
        
        # Get top wards by rainfall
        top_wards = sorted(wards, key=lambda w: w.get("rainfall_total", 0), reverse=True)[:10]
        top_wards_list = [
            {
                "ward_id": w.get("ward_id", ""),
                "ward_name": w.get("ward_name", ""),
                "total_rainfall": w.get("rainfall_total", 0)
            }
            for w in top_wards
        ]
        
        return {
            "county_level_summary": {
                "total_weekly_rainfall": weekly.get("total", 0),
                "daily_breakdown": daily_breakdown,
                "max_daily_intensity": weekly.get("max_intensity", 0),
                "number_of_rainy_days": weekly.get("rainy_days", 0),
                "probability_above_normal": rainfall_data.get("probability_above_normal")
            },
            "ward_level_analysis": [
                {
                    "ward_id": w.get("ward_id", ""),
                    "ward_name": w.get("ward_name", ""),
                    "total_rainfall": w.get("rainfall_total", 0),
                    "number_of_rainy_days": 0,  # Calculate from daily data
                    "peak_intensity_day": "Wednesday"  # Calculate from data
                }
                for w in wards[:20]  # Top 20 wards
            ],
            "top_wards_by_rainfall": top_wards_list,
            "flood_risk_wards": [w.get("ward_id") for w in top_wards[:5]],
            "rainfall_distribution_map": {
                "image_path": "",
                "color_scale": []
            },
            "temporal_patterns": {
                "daily_chart": {
                    "data": [
                        {"day": d["day"][:3], "rainfall": d["rainfall"]}
                        for d in daily_breakdown
                    ]
                },
                "peak_rainfall_days": [],
                "dry_periods": []
            },
            "narrative_description": narrative
        }
    
    def _build_temperature_outlook(self, temp_data: Dict, wards: list, narrative: str) -> Dict:
        """Build temperature outlook section."""
        weekly = temp_data.get("weekly", {})
        daily = temp_data.get("daily", [])
        daily_min = temp_data.get("daily_min", [])
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Find hottest and coolest wards
        hottest_ward = max(wards, key=lambda w: w.get("temp_max", 0), default={})
        coolest_ward = min(wards, key=lambda w: w.get("temp_min", 100), default={})
        
        return {
            "county_level_summary": {
                "mean_weekly_temperature": weekly.get("mean", 0),
                "maximum_temperature": {
                    "value": weekly.get("max", 0),
                    "day": days[daily.index(max(daily))] if daily else "Unknown"
                },
                "minimum_temperature": {
                    "value": weekly.get("min", 0),
                    "day": days[daily_min.index(min(daily_min))] if daily_min else "Unknown"
                },
                "temperature_range": weekly.get("max", 0) - weekly.get("min", 0),
                "daily_mean_temperatures": [
                    {"day": days[i], "mean": (daily[i] + daily_min[i]) / 2}
                    for i in range(min(len(daily), len(daily_min), 7))
                ]
            },
            "ward_level_analysis": [
                {
                    "ward_id": w.get("ward_id", ""),
                    "ward_name": w.get("ward_name", ""),
                    "mean_temperature": w.get("temp_mean", 0),
                    "max_temperature": w.get("temp_max", 0),
                    "min_temperature": w.get("temp_min", 0)
                }
                for w in wards[:20]
            ],
            "hottest_ward": {
                "ward_id": hottest_ward.get("ward_id", ""),
                "ward_name": hottest_ward.get("ward_name", ""),
                "temperature": hottest_ward.get("temp_max", 0)
            },
            "coolest_ward": {
                "ward_id": coolest_ward.get("ward_id", ""),
                "ward_name": coolest_ward.get("ward_name", ""),
                "temperature": coolest_ward.get("temp_min", 0)
            },
            "temperature_distribution_map": {
                "image_path": "",
                "color_scale": []
            },
            "diurnal_patterns": {
                "daytime_highs": [
                    {"day": days[i], "high": daily[i]}
                    for i in range(min(len(daily), 7))
                ],
                "nighttime_lows": [
                    {"day": days[i], "low": daily_min[i]}
                    for i in range(min(len(daily_min), 7))
                ]
            },
            "narrative_description": narrative
        }
    
    def _build_wind_outlook(self, wind_data: Dict, wards: list, narrative: str) -> Dict:
        """Build wind outlook section."""
        weekly = wind_data.get("weekly", {})
        daily_peak = wind_data.get("daily_peak", [])
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Find windiest wards
        windiest_wards = sorted(wards, key=lambda w: w.get("wind_max", 0), reverse=True)[:5]
        
        return {
            "county_level_summary": {
                "mean_wind_speed": weekly.get("mean_speed", 0),
                "maximum_gust": {
                    "value": weekly.get("max_gust", 0),
                    "day": days[daily_peak.index(max(daily_peak))] if daily_peak else "Unknown"
                },
                "dominant_wind_direction": weekly.get("dominant_direction", "N"),
                "daily_peak_wind_speeds": [
                    {"day": days[i], "speed": daily_peak[i]}
                    for i in range(min(len(daily_peak), 7))
                ]
            },
            "ward_level_analysis": [
                {
                    "ward_id": w.get("ward_id", ""),
                    "ward_name": w.get("ward_name", ""),
                    "mean_wind_speed": w.get("wind_mean", 0),
                    "max_gust": w.get("wind_max", 0),
                    "dominant_direction": "NE"  # Calculate from data
                }
                for w in wards[:20]
            ],
            "highest_wind_speed_wards": [
                {
                    "ward_id": w.get("ward_id", ""),
                    "ward_name": w.get("ward_name", ""),
                    "max_gust": w.get("wind_max", 0)
                }
                for w in windiest_wards
            ],
            "wind_speed_distribution_map": {
                "image_path": "",
                "color_scale": []
            },
            "wind_direction_analysis": None,
            "narrative_description": narrative
        }
    
    def _build_ward_visualizations(self) -> Dict:
        """Build ward-level visualizations section."""
        return {
            "rainfall_map": {
                "image_path": "",
                "title": "Rainfall Distribution Map",
                "resolution": "300 DPI",
                "projection": "UTM Zone 37N, EPSG:32637"
            },
            "temperature_map": {
                "image_path": "",
                "title": "Temperature Distribution Map",
                "resolution": "300 DPI",
                "projection": "UTM Zone 37N, EPSG:32637"
            },
            "wind_speed_map": {
                "image_path": "",
                "title": "Wind Speed Distribution Map",
                "resolution": "300 DPI",
                "projection": "UTM Zone 37N, EPSG:32637"
            }
        }
    
    def _build_extreme_values(self, extremes: Dict, wards: list) -> Dict:
        """Build extreme values section."""
        highest_rainfall = extremes.get("highest_rainfall", {})
        hottest = extremes.get("hottest_ward", {})
        coolest = extremes.get("coolest_ward", {})
        windiest = extremes.get("windiest_ward", {})
        flood_risk = extremes.get("flood_risk_wards", [])
        
        return {
            "extreme_events": {
                "highest_single_day_rainfall": {
                    "ward_id": highest_rainfall.get("ward_id", ""),
                    "ward_name": highest_rainfall.get("ward_name", ""),
                    "value": highest_rainfall.get("value", 0),
                    "date": "",
                    "days": highest_rainfall.get("days", [])
                },
                "highest_weekly_rainfall": {
                    "ward_id": highest_rainfall.get("ward_id", ""),
                    "ward_name": highest_rainfall.get("ward_name", ""),
                    "total": highest_rainfall.get("value", 0)
                },
                "hottest_day": {
                    "ward_id": hottest.get("ward_id", ""),
                    "ward_name": hottest.get("ward_name", ""),
                    "temperature": hottest.get("value", 0),
                    "date": "",
                    "day": hottest.get("day")
                },
                "coolest_night": {
                    "ward_id": coolest.get("ward_id", ""),
                    "ward_name": coolest.get("ward_name", ""),
                    "temperature": coolest.get("value", 0),
                    "date": "",
                    "day": coolest.get("day")
                },
                "strongest_wind_gust": {
                    "ward_id": windiest.get("ward_id", ""),
                    "ward_name": windiest.get("ward_name", ""),
                    "speed": windiest.get("value", 0),
                    "date": ""
                }
            },
            "risk_indicators": {
                "flood_risk_wards": [
                    {
                        "ward_id": w.get("ward_id", ""),
                        "ward_name": w.get("ward_name", ""),
                        "risk_level": w.get("risk_level", "moderate"),
                        "reason": f"Total rainfall of {w.get('total_rainfall', 0)}mm exceeds threshold"
                    }
                    for w in flood_risk
                ],
                "heat_stress_warnings": None,
                "wind_advisories": None
            },
            "notable_patterns": []
        }
    
    def _build_methodology(self, metadata: Dict) -> Dict:
        """Build data sources and methodology section."""
        return {
            "forecast_model": {
                "name": "GFS",
                "version": "v15.1",
                "run_date": metadata.get("model_run", ""),
                "forecast_horizon": 7,
                "grid_resolution": metadata.get("grid_resolution", "0.25°")
            },
            "data_processing": {
                "aggregation_method": metadata.get("aggregation_method", "point-in-polygon"),
                "number_of_grid_points": metadata.get("grid_points_used", 0),
                "spatial_interpolation": "Bilinear interpolation",
                "quality_control_measures": ["Data validation", "Outlier detection", "Missing data handling"]
            },
            "observational_data": None,
            "shapefile_sources": {
                "county_boundaries": {
                    "source": "KNBS",
                    "version": "2023",
                    "date": "2023-01-01"
                },
                "ward_boundaries": {
                    "source": "KNBS",
                    "version": "2023",
                    "date": "2023-01-01"
                },
                "coordinate_reference_system": "EPSG:4326"
            },
            "limitations_and_uncertainties": {
                "model_uncertainty": "Forecast accuracy decreases with lead time. Day 1-3 forecasts are most reliable.",
                "spatial_aggregation_limitations": "Ward-level forecasts are derived from 0.25° grid data and may not capture local microclimates.",
                "temporal_resolution_constraints": "Daily averages may miss short-duration extreme events.",
                "ward_level_forecast_accuracy": "Ward-level forecasts have higher uncertainty than county-level averages."
            }
        }
    
    def _build_metadata_disclaimers(self, metadata: Dict) -> Dict:
        """Build metadata and disclaimers section."""
        return {
            "generation_metadata": {
                "report_generation_timestamp": datetime.utcnow().isoformat() + "Z",
                "system_version": metadata.get("system_version", "1.0.0"),
                "processing_duration": metadata.get("processing_duration_seconds"),
                "data_quality_flags": [],
                "warnings": metadata.get("warnings", [])
            },
            "disclaimer_statement": "This report is generated from automated weather forecast data. Ward-level maps are derived from spatial aggregation of global forecasts for planning purposes only. Contact the local meteorological office for official updates and warnings.",
            "copyright_and_attribution": {
                "data_source_attribution": "NOAA/NCEP for GFS",
                "system_attribution": "Clima-scope Automated Weather Reporting System",
                "usage_rights": "For planning and decision-making purposes. Not for official meteorological warnings."
            },
            "contact_information": {
                "meteorological_department": {
                    "name": "Kenya Meteorological Department",
                    "contact": "Contact your local KMD office for official weather warnings"
                },
                "technical_support": {
                    "contact": "support@clima-scope.ke"
                },
                "report_feedback": {
                    "mechanism": "Email feedback to reports@clima-scope.ke"
                }
            }
        }
