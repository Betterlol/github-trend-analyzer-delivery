# GitHub Trend Analyzer Delivery

This repository contains delivery-ready planning artifacts for the GitHub Trend Analyzer project.

## Deliverables
- `docs/PROJECT_OVERVIEW.md`: project scope, goals, phases, KPIs, and risk controls.
- `docs/DEVELOPMENT_GUIDE.md`: implementation guidance, architecture, coding standards, and execution checklist.
- `AGENT_CHARTER.md`: AI objective contract and reasoning constraints.
- `schemas/opportunity_analysis.schema.json`: required structured output schema.
- `docs/VALIDATION_RULES.md`: hard validation gates for evidence balance and confidence calibration.
- `tools/validate_opportunity_output.py`: local validator for model outputs.

## Why these files matter
They ensure the project AI does **not** rely only on GitHub indicators and must include external evidence, counter-evidence, unknowns, and testable next actions.

## Suggested Next Action
Start from `docs/DEVELOPMENT_GUIDE.md` section "Week-by-week Execution Plan" and implement MVP first.
