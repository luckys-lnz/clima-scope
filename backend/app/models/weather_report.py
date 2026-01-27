"""
Weather Report Model

Stores raw CountyWeatherReport JSON data from GFS processing.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from ..database import Base


class WeatherReport(Base):
    """Raw weather report data from GFS forecast."""
    
    __tablename__ = "weather_reports"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to county
    county_id = Column(String(2), ForeignKey("counties.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Report period
    period_start = Column(DateTime, nullable=False, index=True, comment="Report period start date")
    period_end = Column(DateTime, nullable=False, index=True, comment="Report period end date")
    week_number = Column(Integer, nullable=True, comment="ISO week number (1-53)")
    year = Column(Integer, nullable=False, index=True, comment="Year")
    
    # Raw JSON data (CountyWeatherReport schema)
    raw_data = Column(JSON, nullable=False, comment="Complete CountyWeatherReport JSON")
    
    # Metadata from raw_data
    schema_version = Column(String(10), nullable=False, default="1.0", comment="Schema version")
    model_run_timestamp = Column(DateTime, nullable=True, comment="GFS model run timestamp")
    data_source = Column(String(100), nullable=True, comment="Data source (e.g., 'GFS v15.1')")
    
    # Quality flags
    quality_overall = Column(String(20), nullable=True, comment="Overall quality: excellent, good, fair, degraded")
    quality_missing_data_percent = Column(Integer, nullable=True, comment="Percentage of missing data")
    quality_spatial_coverage_percent = Column(Integer, nullable=True, comment="Percentage of wards with valid data")
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False, index=True, comment="Whether report has been processed into CompleteReport")
    processing_error = Column(Text, nullable=True, comment="Error message if processing failed")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    county = relationship("County", back_populates="weather_reports")
    complete_report = relationship("CompleteReport", back_populates="weather_report", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_weather_report_county_period", "county_id", "period_start", "period_end"),
        Index("idx_weather_report_year_week", "year", "week_number"),
    )
    
    def __repr__(self):
        return f"<WeatherReport(id={self.id}, county_id={self.county_id}, period={self.period_start.date()})>"
    
    def get_raw_data(self) -> Dict[str, Any]:
        """Get raw data as dictionary."""
        return self.raw_data if isinstance(self.raw_data, dict) else {}
