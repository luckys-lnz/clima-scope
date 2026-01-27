"""
Complete Report Model

Stores AI-generated CompleteWeatherReport JSON with narrative content.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from ..database import Base


class CompleteReport(Base):
    """Complete weather report with AI-generated narratives."""
    
    __tablename__ = "complete_reports"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to raw weather report
    weather_report_id = Column(
        Integer,
        ForeignKey("weather_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Reference to source WeatherReport"
    )
    
    # Report period (denormalized for easier querying)
    county_id = Column(String(2), ForeignKey("counties.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    week_number = Column(Integer, nullable=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Complete report JSON data (CompleteWeatherReport schema)
    report_data = Column(JSON, nullable=False, comment="Complete CompleteWeatherReport JSON with narratives")
    
    # AI generation metadata
    ai_provider = Column(String(20), nullable=True, comment="AI provider used: openai, anthropic")
    ai_model = Column(String(50), nullable=True, comment="AI model used (e.g., gpt-4o, claude-3-5-sonnet)")
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When report was generated")
    generation_duration_seconds = Column(Integer, nullable=True, comment="Time taken to generate report")
    
    # Status
    is_published = Column(Boolean, default=False, nullable=False, index=True, comment="Whether report is published")
    published_at = Column(DateTime, nullable=True, comment="When report was published")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    weather_report = relationship("WeatherReport", back_populates="complete_report")
    county = relationship("County")
    pdf_reports = relationship("PDFReport", back_populates="complete_report", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_complete_report_county_period", "county_id", "period_start", "period_end"),
        Index("idx_complete_report_published", "is_published", "published_at"),
    )
    
    def __repr__(self):
        return f"<CompleteReport(id={self.id}, weather_report_id={self.weather_report_id}, county_id={self.county_id})>"
    
    def get_report_data(self) -> Dict[str, Any]:
        """Get report data as dictionary."""
        return self.report_data if isinstance(self.report_data, dict) else {}
