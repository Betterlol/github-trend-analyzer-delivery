#!/usr/bin/env python3
"""Rule-based validator for LLM opportunity analysis output.

Usage:
  python tools/validate_opportunity_output.py output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.services.validator import validate_payload


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

    result = validate_payload(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
