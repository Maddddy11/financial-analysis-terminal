"""MPBF Agent (Tandon Committee methodology).

Computes Maximum Permissible Bank Finance (MPBF) deterministically from the
latest current assets and current liabilities values in OCR JSON output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _latest_numeric(series: Any) -> float | None:
    if not isinstance(series, list):
        return None
    for item in reversed(series):
        if not isinstance(item, dict):
            continue
        val = item.get("value")
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return None


def _method_first(current_assets: float, current_liabilities: float) -> dict[str, Any]:
    working_capital_gap = current_assets - current_liabilities
    mpbf_limit = 0.75 * working_capital_gap
    borrower_contribution_required = working_capital_gap - mpbf_limit
    compliance_status = "COMPLIANT" if mpbf_limit >= 0 else "NON_COMPLIANT"
    return {
        "method": "FIRST_METHOD",
        "working_capital_gap": float(working_capital_gap),
        "borrower_contribution_required": float(borrower_contribution_required),
        "mpbf_limit": float(max(0.0, mpbf_limit)),
        "compliance_status": compliance_status,
    }


def _method_second(current_assets: float, current_liabilities: float) -> dict[str, Any]:
    working_capital_gap = current_assets - current_liabilities
    borrower_contribution_required = 0.25 * current_assets
    mpbf_limit = working_capital_gap - borrower_contribution_required
    compliance_status = "COMPLIANT" if mpbf_limit >= 0 else "NON_COMPLIANT"
    return {
        "method": "SECOND_METHOD",
        "working_capital_gap": float(working_capital_gap),
        "borrower_contribution_required": float(borrower_contribution_required),
        "mpbf_limit": float(max(0.0, mpbf_limit)),
        "compliance_status": compliance_status,
    }


def run_mpbf_agent(json_path: str | Path) -> dict[str, Any]:
    path = Path(json_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    ts = payload.get("time_series") or {}

    current_assets = _latest_numeric(ts.get("current_assets"))
    current_liabilities = _latest_numeric(ts.get("current_liabilities"))
    if current_assets is None or current_liabilities is None:
        raise ValueError("Missing required fields: current_assets/current_liabilities")
    if current_assets < 0 or current_liabilities < 0:
        raise ValueError("current_assets/current_liabilities cannot be negative")

    first_method = _method_first(current_assets, current_liabilities)
    second_method = _method_second(current_assets, current_liabilities)

    rec = second_method
    narrative = (
        "MPBF assessed using Tandon Committee methods. "
        f"Under RBI-preferred Second Method, working capital gap is {rec['working_capital_gap']:.2f}, "
        f"borrower contribution required is {rec['borrower_contribution_required']:.2f}, "
        f"and maximum permissible bank finance is {rec['mpbf_limit']:.2f}."
    )

    return {
        "entity": payload.get("entity", {}).get("entity_id", "UNKNOWN"),
        "metrics": {
            "current_assets": float(current_assets),
            "current_liabilities": float(current_liabilities),
            "first_method": first_method,
            "second_method": second_method,
            "recommended_method": "SECOND_METHOD",
            "recommended_mpbf_limit": float(second_method["mpbf_limit"]),
            "recommended_compliance_status": str(second_method["compliance_status"]),
        },
        "analysis": narrative,
    }
