"""
Map Storage Service

Manages storage, retrieval, and metadata for weather map images generated
by the geospatial processing pipeline (Person A's work).

File Naming Convention:
    {county_id}_{variable}_{period_start}_{period_end}.png
    Example: 31_rainfall_2026-01-27_2026-02-02.png

Directory Structure:
    data/maps/{county_id}/{year}/{week}/
    Example: data/maps/31/2026/05/
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class MapVariable(str, Enum):
    """Weather variables that can be mapped."""
    RAINFALL = "rainfall"
    TEMPERATURE = "temperature"
    WIND = "wind"


class MapFormat(str, Enum):
    """Supported map image formats."""
    PNG = "png"
    SVG = "svg"
    JPEG = "jpeg"


class MapStorageError(Exception):
    """Base exception for map storage operations."""
    pass


class MapMetadata:
    """Metadata for a weather map."""
    
    def __init__(
        self,
        county_id: str,
        variable: MapVariable,
        period_start: str,
        period_end: str,
        file_path: Path,
        format: MapFormat = MapFormat.PNG,
        resolution_dpi: int = 300,
        width_px: int = 1200,
        height_px: int = 900,
        generated_at: Optional[datetime] = None,
        bounds: Optional[Dict[str, float]] = None,
        quality_flags: Optional[List[str]] = None,
        **kwargs
    ):
        self.county_id = county_id
        self.variable = variable
        self.period_start = period_start
        self.period_end = period_end
        self.file_path = file_path
        self.format = format
        self.resolution_dpi = resolution_dpi
        self.width_px = width_px
        self.height_px = height_px
        self.generated_at = generated_at or datetime.utcnow()
        self.bounds = bounds or {}
        self.quality_flags = quality_flags or []
        self.extra = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "county_id": self.county_id,
            "variable": self.variable.value,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "file_path": str(self.file_path),
            "format": self.format.value,
            "resolution_dpi": self.resolution_dpi,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "generated_at": self.generated_at.isoformat(),
            "bounds": self.bounds,
            "quality_flags": self.quality_flags,
            **self.extra
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapMetadata':
        """Create metadata from dictionary."""
        return cls(
            county_id=data["county_id"],
            variable=MapVariable(data["variable"]),
            period_start=data["period_start"],
            period_end=data["period_end"],
            file_path=Path(data["file_path"]),
            format=MapFormat(data["format"]),
            resolution_dpi=data.get("resolution_dpi", 300),
            width_px=data.get("width_px", 1200),
            height_px=data.get("height_px", 900),
            generated_at=datetime.fromisoformat(data["generated_at"]),
            bounds=data.get("bounds"),
            quality_flags=data.get("quality_flags", [])
        )


class MapStorageService:
    """Service for managing weather map storage."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize map storage service.
        
        Args:
            base_path: Base directory for map storage (defaults to data/maps)
        """
        if base_path is None:
            # Default to project_root/data/maps
            project_root = Path(__file__).parent.parent.parent.parent
            base_path = project_root / "data" / "maps"
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("map_storage_initialized", base_path=str(self.base_path))
    
    def _build_file_name(
        self,
        county_id: str,
        variable: MapVariable,
        period_start: str,
        period_end: str,
        format: MapFormat = MapFormat.PNG
    ) -> str:
        """
        Build standardized file name.
        
        Format: {county_id}_{variable}_{period_start}_{period_end}.{ext}
        Example: 31_rainfall_2026-01-27_2026-02-02.png
        """
        return f"{county_id}_{variable.value}_{period_start}_{period_end}.{format.value}"
    
    def _build_storage_path(
        self,
        county_id: str,
        period_start: str,
        ensure_exists: bool = True
    ) -> Path:
        """
        Build storage directory path.
        
        Structure: {base_path}/{county_id}/{year}/{week}/
        Example: data/maps/31/2026/05/
        """
        # Parse period_start to extract year and week
        try:
            date = datetime.fromisoformat(period_start)
            year = date.year
            # ISO week number
            week = date.isocalendar()[1]
        except ValueError:
            raise MapStorageError(f"Invalid period_start format: {period_start}")
        
        storage_dir = self.base_path / county_id / str(year) / f"{week:02d}"
        
        if ensure_exists:
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        return storage_dir
    
    def _metadata_path(self, map_file_path: Path) -> Path:
        """Get metadata JSON path for a map file."""
        return map_file_path.with_suffix(".meta.json")
    
    def store_map(
        self,
        source_file: Path,
        county_id: str,
        variable: MapVariable,
        period_start: str,
        period_end: str,
        format: MapFormat = MapFormat.PNG,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False
    ) -> MapMetadata:
        """
        Store a weather map image.
        
        Args:
            source_file: Path to source image file
            county_id: KNBS county code (e.g., "31")
            variable: Weather variable (rainfall, temperature, wind)
            period_start: Period start date (ISO format: YYYY-MM-DD)
            period_end: Period end date (ISO format: YYYY-MM-DD)
            format: Image format
            metadata: Optional additional metadata
            overwrite: Whether to overwrite existing file
            
        Returns:
            MapMetadata object
            
        Raises:
            MapStorageError: If file operations fail
        """
        if not source_file.exists():
            raise MapStorageError(f"Source file not found: {source_file}")
        
        # Build storage path
        storage_dir = self._build_storage_path(county_id, period_start)
        file_name = self._build_file_name(county_id, variable, period_start, period_end, format)
        dest_path = storage_dir / file_name
        
        # Check if file exists
        if dest_path.exists() and not overwrite:
            logger.warning("map_already_exists", dest_path=str(dest_path))
            # Load existing metadata
            meta_path = self._metadata_path(dest_path)
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    return MapMetadata.from_dict(json.load(f))
            else:
                raise MapStorageError(f"Map exists but metadata missing: {dest_path}")
        
        # Copy file
        try:
            shutil.copy2(source_file, dest_path)
            logger.info("map_stored", dest_path=str(dest_path), size_bytes=dest_path.stat().st_size)
        except Exception as e:
            raise MapStorageError(f"Failed to copy map file: {e}")
        
        # Create metadata
        map_metadata = MapMetadata(
            county_id=county_id,
            variable=variable,
            period_start=period_start,
            period_end=period_end,
            file_path=dest_path,
            format=format,
            **(metadata or {})
        )
        
        # Save metadata
        meta_path = self._metadata_path(dest_path)
        try:
            with open(meta_path, 'w') as f:
                json.dump(map_metadata.to_dict(), f, indent=2)
            logger.info("map_metadata_saved", meta_path=str(meta_path))
        except Exception as e:
            logger.error("map_metadata_save_failed", error=str(e))
            # Don't fail the operation, metadata is optional
        
        return map_metadata
    
    def get_map(
        self,
        county_id: str,
        variable: MapVariable,
        period_start: str,
        period_end: str,
        format: MapFormat = MapFormat.PNG
    ) -> Optional[MapMetadata]:
        """
        Retrieve map metadata.
        
        Returns:
            MapMetadata if found, None otherwise
        """
        storage_dir = self._build_storage_path(county_id, period_start, ensure_exists=False)
        file_name = self._build_file_name(county_id, variable, period_start, period_end, format)
        map_path = storage_dir / file_name
        
        if not map_path.exists():
            logger.debug("map_not_found", map_path=str(map_path))
            return None
        
        # Load metadata
        meta_path = self._metadata_path(map_path)
        if meta_path.exists():
            try:
                with open(meta_path, 'r') as f:
                    return MapMetadata.from_dict(json.load(f))
            except Exception as e:
                logger.warning("map_metadata_load_failed", error=str(e))
        
        # Return basic metadata if metadata file missing
        return MapMetadata(
            county_id=county_id,
            variable=variable,
            period_start=period_start,
            period_end=period_end,
            file_path=map_path,
            format=format
        )
    
    def list_maps(
        self,
        county_id: Optional[str] = None,
        variable: Optional[MapVariable] = None,
        year: Optional[int] = None,
        week: Optional[int] = None
    ) -> List[MapMetadata]:
        """
        List stored maps with optional filters.
        
        Args:
            county_id: Filter by county
            variable: Filter by weather variable
            year: Filter by year
            week: Filter by ISO week number
            
        Returns:
            List of MapMetadata objects
        """
        maps = []
        
        # Build search path
        if county_id and year and week:
            # Specific directory
            search_dirs = [self.base_path / county_id / str(year) / f"{week:02d}"]
        elif county_id:
            # All years/weeks for county
            county_path = self.base_path / county_id
            if county_path.exists():
                search_dirs = [p for p in county_path.rglob("*/") if p.is_dir()]
            else:
                search_dirs = []
        else:
            # All maps
            search_dirs = [p for p in self.base_path.rglob("*/") if p.is_dir()]
        
        # Find map files
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for map_file in search_dir.glob("*.png"):
                # Skip metadata files
                if map_file.name.endswith(".meta.json"):
                    continue
                
                # Load metadata
                meta_path = self._metadata_path(map_file)
                if meta_path.exists():
                    try:
                        with open(meta_path, 'r') as f:
                            meta = MapMetadata.from_dict(json.load(f))
                        
                        # Apply filters
                        if variable and meta.variable != variable:
                            continue
                        
                        maps.append(meta)
                    except Exception as e:
                        logger.warning("map_metadata_load_failed", file=str(map_file), error=str(e))
        
        return sorted(maps, key=lambda m: m.generated_at, reverse=True)
    
    def delete_map(
        self,
        county_id: str,
        variable: MapVariable,
        period_start: str,
        period_end: str,
        format: MapFormat = MapFormat.PNG
    ) -> bool:
        """
        Delete a stored map and its metadata.
        
        Returns:
            True if deleted, False if not found
        """
        storage_dir = self._build_storage_path(county_id, period_start, ensure_exists=False)
        file_name = self._build_file_name(county_id, variable, period_start, period_end, format)
        map_path = storage_dir / file_name
        
        if not map_path.exists():
            return False
        
        # Delete map file
        try:
            map_path.unlink()
            logger.info("map_deleted", map_path=str(map_path))
        except Exception as e:
            raise MapStorageError(f"Failed to delete map: {e}")
        
        # Delete metadata
        meta_path = self._metadata_path(map_path)
        if meta_path.exists():
            try:
                meta_path.unlink()
                logger.info("map_metadata_deleted", meta_path=str(meta_path))
            except Exception as e:
                logger.warning("map_metadata_delete_failed", error=str(e))
        
        return True
    
    def get_maps_for_report(
        self,
        county_id: str,
        period_start: str,
        period_end: str
    ) -> Dict[str, Optional[MapMetadata]]:
        """
        Get all maps (rainfall, temperature, wind) for a report period.
        
        Returns:
            Dict with keys: rainfall, temperature, wind
            Values are MapMetadata or None if not found
        """
        return {
            "rainfall": self.get_map(county_id, MapVariable.RAINFALL, period_start, period_end),
            "temperature": self.get_map(county_id, MapVariable.TEMPERATURE, period_start, period_end),
            "wind": self.get_map(county_id, MapVariable.WIND, period_start, period_end),
        }
