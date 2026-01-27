"""
Ward Model

Represents a ward within a county.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Ward(Base):
    """Ward model for sub-county administrative units."""
    
    __tablename__ = "wards"
    
    # Primary key: Ward ID (typically ward code)
    id = Column(String(50), primary_key=True, comment="Ward identifier/code")
    name = Column(String(200), nullable=False, comment="Ward name")
    
    # Foreign key to county
    county_id = Column(String(2), ForeignKey("counties.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Optional metadata
    sub_county = Column(String(100), nullable=True, comment="Sub-county name")
    area_km2 = Column(Integer, nullable=True, comment="Area in square kilometers")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True, comment="Additional notes or metadata")
    
    # Relationships
    county = relationship("County", back_populates="wards")
    
    def __repr__(self):
        return f"<Ward(id={self.id}, name={self.name}, county_id={self.county_id})>"
