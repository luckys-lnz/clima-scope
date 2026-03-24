"""Fixups that keep Geospatial libs working together."""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def ensure_fiona_path():
    """Ensure ``fiona.path`` exists for modules expecting it."""
    try:
        import fiona
    except ImportError:
        return

    if hasattr(fiona, "path"):
        return

    # Fiona 1.10 removed ``fiona.path`` while some GeoPandas/GDAL helpers still
    # import it. Point the attribute to pathlib.Path so those imports do not fail.
    fiona.path = Path
