"""MPBF (Maximum Permissible Bank Finance) Agent.

Deterministic implementation of Tandon Committee Method I and Method II.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _latest_value(series: Any) -> float | None:
    if not isinstance(series, list):
        return None
    for item in reversed(series):
        if isinstance(item, dict) and item.get("value") is not None:
            try:
                return float(item["value"])
            except (TypeError, ValueError):
                continue
    return None


def _calc_methods(current_assets: float, current_liabilities: float) -> dict[str, Any]:
    wc_gap = current_assets - current_liabilities
    borrower_contribution = 0.25 * current_assets

    first_mpbf = 0.75 * wc_gap
    second_mpbf = wc_gap - borrower_contribution

    first_limit = max(0.0, first_mpbf)
    second_limit = max(0.0, second_mpbf)

    compliance_status = "COMPLIANT" if second_mpbf > 0 else "NON_COMPLIANT"

    return {
        "working_capital_gap": round(wc_gap, 2),
        "borrower_contribution_required": round(borrower_contribution, 2),
        "first_method": {
            "method": "Tandon Method I",
            "formula": "75% × (Current Assets - Current Liabilities)",
            "mpbf_limit": round(first_limit, 2),
        },
        "second_method": {
            "method": "Tandon Method II (RBI Preferred)",
            "formula": "(Current Assets - Current Liabilities) - 25% of Current Assets",
            "mpbf_limit": round(second_limit, 2),
        },
        "recommended_method": "second_method",
        "compliance_status": compliance_status,
    }


def run(
    *,
    json_path: str | Path,
    base_url: str,
    model: str,
    api_key: str = "local",
) -> dict[str, Any]:
    """Run MPBF calculation from JSON payload.

    base_url/model/api_key are accepted for interface parity with other agents.
    """
    _ = (base_url, model, api_key)

    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    ts = payload.get("time_series") or {}

    current_assets = _latest_value(ts.get("current_assets"))
    current_liabilities = _latest_value(ts.get("current_liabilities"))

    if current_assets is None or current_liabilities is None:
        missing = []
        if current_assets is None:
            missing.append("current_assets")
        if current_liabilities is None:
            missing.append("current_liabilities")
        return {"error": f"MPBF Agent skipped — missing: {', '.join(missing)}"}

    metrics = _calc_methods(current_assets=current_assets, current_liabilities=current_liabilities)
    second = metrics["second_method"]["mpbf_limit"]
    status = metrics["compliance_status"]

    analysis = (
        f"MPBF was evaluated using Tandon Method I and the RBI-preferred Method II. "
        f"Based on Method II, the maximum permissible bank finance is {second:,.2f}. "
        f"The borrower must contribute 25% of current assets from long-term sources. "
        f"Overall MPBF status is {status} under Method II."
    )

    return {
        "entity": payload.get("entity", {}).get("entity_id", "UNKNOWN"),
        "metrics": metrics,
        "analysis": analysis,
    }

