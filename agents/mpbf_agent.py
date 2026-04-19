"""MPBF Agent wrapper for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.mpbf_agent import run_mpbf_agent


def run(
    *,
    json_path: str | Path,
    base_url: str,
    model: str,
    api_key: str = "local",
) -> dict[str, Any]:
    """Run the deterministic MPBF agent from an OCR output JSON file."""
    _ = (base_url, model, api_key)
    return run_mpbf_agent(Path(json_path))

