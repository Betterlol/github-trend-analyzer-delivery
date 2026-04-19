#!/usr/bin/env python3
"""Rule-based validator for LLM opportunity analysis output.

Usage:
  python tools/validate_opportunity_output.py output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/validate_opportunity_output.py <output.json>")
        return 2

    payload_path = Path(sys.argv[1])
    if not payload_path.exists():
        print(json.dumps({"valid": False, "status": "needs_revision", "errors": ["file not found"], "warnings": []}, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(json.dumps({"valid": False, "status": "needs_revision", "errors": [f"invalid json: {exc}"], "warnings": []}, ensure_ascii=False))
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    github_signals = payload.get("github_signals", [])
    external_signals = payload.get("external_signals", [])
    counter_evidence = payload.get("counter_evidence", [])
    unknowns = payload.get("unknowns", [])
    next_steps = payload.get("next_validation_steps", [])
    confidence = payload.get("confidence")

    if len(github_signals) < 3:
        errors.append("github_signals count < 3")
    if len(external_signals) < 2:
        errors.append("external_signals count < 2")
    if len(counter_evidence) < 2:
        errors.append("counter_evidence count < 2")
    if len(unknowns) < 2:
        errors.append("unknowns count < 2")
    if len(next_steps) < 2:
        errors.append("next_validation_steps count < 2")

    if not isinstance(confidence, (int, float)):
        errors.append("confidence missing or not numeric")
    else:
        if confidence < 0 or confidence > 1:
            errors.append("confidence out of range [0,1]")

    strong_external = sum(1 for s in external_signals if isinstance(s, dict) and s.get("strength") == "strong")
    high_severity_risks = [r for r in counter_evidence if isinstance(r, dict) and r.get("severity") == "high"]

    if isinstance(confidence, (int, float)) and confidence > 0.8 and strong_external < 3:
        errors.append("confidence > 0.8 but strong external signals < 3")

    if high_severity_risks and len(next_steps) == 0:
        errors.append("high severity risks present without mitigation steps")

    if len(external_signals) == 0 and len(github_signals) > 0:
        warnings.append("output appears GitHub-only; add external evidence")

    valid = len(errors) == 0
    status = "ok" if valid else "needs_revision"

    print(json.dumps({"valid": valid, "status": status, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
