import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def _render_path(path_parts: list[object]) -> str:
    if not path_parts:
        return "$"
    return "$." + ".".join(str(part) for part in path_parts)


def load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path:
        target = schema_path
    else:
        target = Path(__file__).resolve().parents[2] / "schemas" / "opportunity_analysis.schema.json"
    return json.loads(target.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], schema_path: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)

    schema_errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    for err in schema_errors:
        errors.append(f"schema violation at {_render_path(list(err.path))}: {err.message}")

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
    elif confidence < 0 or confidence > 1:
        errors.append("confidence out of range [0,1]")

    strong_external = sum(1 for s in external_signals if isinstance(s, dict) and s.get("strength") == "strong")
    if isinstance(confidence, (int, float)) and confidence > 0.8 and strong_external < 3:
        errors.append("confidence > 0.8 but strong external signals < 3")

    high_risk_ids = {
        risk.get("id")
        for risk in counter_evidence
        if isinstance(risk, dict) and risk.get("severity") == "high" and isinstance(risk.get("id"), str)
    }
    mitigated_risk_ids: set[str] = set()
    for step in next_steps:
        if not isinstance(step, dict):
            continue
        addresses = step.get("addresses_risks", [])
        if isinstance(addresses, list):
            mitigated_risk_ids.update(risk for risk in addresses if isinstance(risk, str))

    unresolved = sorted(high_risk_ids - mitigated_risk_ids)
    if unresolved:
        errors.append(f"high severity risks not mitigated in next_validation_steps: {', '.join(unresolved)}")

    if len(external_signals) == 0 and len(github_signals) > 0:
        errors.append("output appears GitHub-only; add external evidence")

    valid = not errors
    status = "ok" if valid else "needs_revision"
    return {"valid": valid, "status": status, "errors": errors, "warnings": warnings}

