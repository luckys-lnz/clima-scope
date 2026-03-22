"""Thin bridge to the script-based PDF renderer in backend/scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional


_PDF_SCRIPT_MODULE_NAME = "_clima_scope_pdf_renderer_runtime"


def _load_pdf_script_module() -> ModuleType:
    """
    Load backend/scripts/pdf_renderer.py directly from file.
    """
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "pdf_renderer.py"
    if not script_path.exists():
        raise FileNotFoundError(f"PDF renderer script not found: {script_path}")

    spec = importlib.util.spec_from_file_location(_PDF_SCRIPT_MODULE_NAME, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec from: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[_PDF_SCRIPT_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def generate_weekly_forecast_pdf(
    data: Dict[str, Any],
    narration: Dict[str, Any],
    map_path: Optional[str],
    output_path: str,
    signoff: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Delegate to backend/scripts/pdf_renderer.py.
    """
    module = _load_pdf_script_module()
    generate_fn = getattr(module, "generate_weekly_forecast_pdf", None)
    if not callable(generate_fn):
        raise AttributeError("generate_weekly_forecast_pdf not found in scripts/pdf_renderer.py")

    return generate_fn(
        data=data,
        narration=narration,
        map_path=map_path,
        output_path=output_path,
        signoff=signoff or {},
    )
