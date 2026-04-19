# Validation Rules for LLM Opportunity Analysis

This document defines hard checks that prevent the model from over-relying on GitHub metrics.

## Rule Groups

## A. Structural Rules
- Output must satisfy `schemas/opportunity_analysis.schema.json`.
- If schema fails -> set `status=needs_revision`.

## B. Evidence Balance Rules (hard gate)
- `github_signals` count >= 3
- `external_signals` count >= 2
- `counter_evidence` count >= 2
- `unknowns` count >= 2

If any check fails -> reject as incomplete.

## C. Confidence Calibration Rules
- `confidence` must be between 0 and 1.
- If `confidence > 0.80` and strong external signals < 3 -> reject.
- If `confidence > 0.80` and any `counter_evidence.severity == "high"` without mitigation in `next_validation_steps` -> reject.

## D. Anti-Hype Rules
- If top reasoning is only stars/forks and no external signal -> reject.
- If no bear-case or counter-evidence -> reject.
- If no measurable next validation action -> reject.

## E. Actionability Rules
Each `next_validation_steps` item must include:
- concrete action
- measurable success metric
- owner
- timebox (days)

## Reference Validator Behavior
Return object:
```json
{
  "valid": false,
  "status": "needs_revision",
  "errors": ["external_signals count < 2", "missing bear-case mitigation"],
  "warnings": []
}
```

## Minimal Acceptance Checklist
- [ ] Balanced evidence (GitHub + external)
- [ ] Contrarian view included (bear case)
- [ ] Unknowns explicit
- [ ] Confidence calibrated
- [ ] Next steps testable
