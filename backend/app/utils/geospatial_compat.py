"""Fixups that keep Geospatial libs working together."""

from functools import lru_cache
import warnings
import sys
import types


def _build_fiona_path_module():
    """Rebuild the deprecated ``fiona.path`` module from ``fiona._path``."""
    try:
        import fiona._path as _path
        from fiona.errors import FionaDeprecationWarning
    except ImportError:
        return None

    module = types.ModuleType("fiona.path")
    module.__all__ = ["ParsedPath", "UnparsedPath", "parse_path", "vsi_path"]
    module.ParsedPath = _path._ParsedPath
    module.UnparsedPath = _path._UnparsedPath
    module.parse_path = _path._parse_path
    module.vsi_path = _path._vsi_path
    module.__doc__ = "Deprecated compatibility shim that mirrors ``fiona.path``."

    warnings.warn(
        "fiona.path shim enabled for backward compatibility.",
        FionaDeprecationWarning,
        stacklevel=3,
    )
    return module


@lru_cache(maxsize=1)
def ensure_fiona_path():
    """Ensure ``fiona.path`` exists for modules expecting it."""
    try:
        import fiona
    except ImportError:
        return

    if getattr(fiona, "path", None) and isinstance(fiona.path, types.ModuleType):
        return

    module = _build_fiona_path_module()
    if not module:
        return

    fiona.path = module
    sys.modules.setdefault("fiona.path", module)
