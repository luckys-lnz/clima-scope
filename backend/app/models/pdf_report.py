"""
PDF Report Model

Stores metadata about generated PDF files.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Index, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class PDFReport(Base):
    """Metadata for generated PDF reports."""
    
    __tablename__ = "pdf_reports"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to complete report
    complete_report_id = Column(
        Integer,
        ForeignKey("complete_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to CompleteReport"
    )
    
    # File information
    file_path = Column(String(500), nullable=False, unique=True, comment="Path to PDF file")
    file_name = Column(String(255), nullable=False, comment="PDF filename")
    file_size_bytes = Column(BigInteger, nullable=True, comment="File size in bytes")
    
    # Generation metadata
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    generation_duration_seconds = Column(Integer, nullable=True, comment="Time taken to generate PDF")
    
    # Status
    is_available = Column(String(20), default="available", nullable=False, index=True, comment="Status: available, deleted, archived")
    
    # Access tracking
    download_count = Column(Integer, default=0, nullable=False, comment="Number of times downloaded")
    last_downloaded_at = Column(DateTime, nullable=True, comment="Last download timestamp")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    complete_report = relationship("CompleteReport", back_populates="pdf_reports")
    
    # Indexes
    __table_args__ = (
        Index("idx_pdf_report_complete_report", "complete_report_id"),
        Index("idx_pdf_report_generated", "generated_at"),
        Index("idx_pdf_report_status", "is_available"),
    )
    
    def __repr__(self):
        return f"<PDFReport(id={self.id}, file_name={self.file_name}, complete_report_id={self.complete_report_id})>"
