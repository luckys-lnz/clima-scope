"""
County Model

Represents a county in Kenya with KNBS codes.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class County(Base):
    """County model for Kenya administrative units."""
    
    __tablename__ = "counties"
    
    # Primary key: KNBS 2-digit code
    id = Column(String(2), primary_key=True, comment="KNBS county code (2-digit)")
    name = Column(String(100), nullable=False, unique=True, comment="Official county name")
    region = Column(String(50), nullable=True, comment="Region name (e.g., 'Nairobi', 'Coast')")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True, comment="Additional notes or metadata")
    
    # Relationships
    wards = relationship("Ward", back_populates="county", cascade="all, delete-orphan")
    weather_reports = relationship("WeatherReport", back_populates="county", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<County(id={self.id}, name={self.name})>"
