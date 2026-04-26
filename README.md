# GitHub Trend Analyzer Delivery

This repository now includes both:
- delivery-ready planning artifacts (docs + schema + rules), and
- a runnable MVP implementation (`FastAPI + SQLite + CLI + validator`).

## What Is Included
- `docs/PROJECT_OVERVIEW.md`: scope, goals, phases, KPIs, and risk controls.
- `docs/DEVELOPMENT_GUIDE.md`: implementation plan and release checklist.
- `AGENT_CHARTER.md`: objective contract and reasoning constraints.
- `schemas/opportunity_analysis.schema.json`: strict output contract.
- `docs/VALIDATION_RULES.md`: hard gates for evidence balance and confidence.
- `tools/validate_opportunity_output.py`: local validator CLI.
- `app/`: MVP code (collector, scorer, insight generation, API/CLI, persistence).
- `tests/`: baseline smoke tests.

## Framework Adjustments Applied
- Added explicit risk IDs in `counter_evidence` (e.g., `R01`).
- Added `next_validation_steps[*].addresses_risks` for mitigation traceability.
- Upgraded validator to enforce JSON Schema + rule checks together.
- Enforced high-severity risk mitigation mapping before accepting outputs.

## Quick Start
1. Create virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
2. Run API:
```bash
uvicorn app.main:app --reload
```
Web UI: open `http://127.0.0.1:8000/`
3. Run CLI (offline sample mode):
```bash
python -m app.cli analyze --topic ai --limit 5 --offline
```
4. Validate one output file:
```bash
python tools/validate_opportunity_output.py output.json
```
5. Run tests:
```bash
pytest
```

## Environment Variables
- `GITHUB_TOKEN`: optional, recommended for higher GitHub API quota.
- `DATABASE_URL`: optional, defaults to `sqlite:////tmp/trend_analyzer.db` (Vercel-safe writable path).
- `LLM_ENABLED`: default `true`. If `false`, insight generation uses deterministic fallback template.
- `LLM_API_KEY` or `OPENAI_API_KEY`: enables LLM opportunity generation.
- `LLM_BASE_URL` or `OPENAI_BASE_URL`: defaults to `https://api.openai.com/v1` (OpenAI-compatible endpoint).
- `LLM_MODEL` or `OPENAI_MODEL`: defaults to `gpt-4o-mini`.
- `LLM_TIMEOUT_SEC`: request timeout for each LLM call (default `45`).
- `LLM_MAX_RETRIES`: validation-feedback retries before fallback (default `2`).

## API Endpoints
- `GET /health`: service health check.
- `POST /analyze`: run topic analysis (`topic`, `limit`, `offline`) and return ranked repos + opportunities.
- `GET /dashboard`: return repository inventory, language mix, recent runs, and recent analyses for UI dashboard.

## LLM Generation Flow
1. Build repository context and scoring summary.
2. Call LLM for strict JSON output.
3. Validate against schema and hard rules.
4. If invalid, retry with explicit validation errors as feedback.
5. If still invalid (or LLM unavailable), fallback to deterministic template output.
