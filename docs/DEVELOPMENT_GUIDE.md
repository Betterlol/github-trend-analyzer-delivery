# Development Guide: GitHub Trend Analyzer

## 1) Recommended Stack
- Language: Python 3.11+
- API/Service: FastAPI
- Storage: PostgreSQL (SQLite allowed in MVP local mode)
- Async HTTP: httpx/aiohttp
- Validation: Pydantic
- UI: Streamlit or simple web frontend
- Testing: pytest
- Delivery: Docker + GitHub Actions

## 2) Reference Architecture
1. Collector
- Query GitHub Search API by topic/language/time window.
- Handle paging, retry, and quota-safe throttling.

2. Processor
- Normalize repo metadata.
- Extract language, update recency, contributor activity, and release cadence.

3. Scorer
- Compute three axes:
  - Heat: current attention signals.
  - Potential: growth/novelty and momentum.
  - Buildability: practical room for implementation and differentiation.

4. Insight Engine
- LLM classification and concise recommendation rationale.
- Force JSON schema output and retry on invalid response.

5. Presentation Layer
- Filters by domain/language/time horizon.
- Show score breakdown + "why this is worth building" summary.

## 3) Data Model (minimum)
- `repos(id, full_name, url, language, created_at, updated_at, stars, forks, watchers)`
- `repo_metrics(repo_id, commit_30d, contributors_30d, releases_90d, issue_close_rate)`
- `repo_analysis(repo_id, category, tags, rationale, confidence, analyzed_at)`
- `pipeline_runs(run_id, stage, status, duration_ms, error_message, created_at)`

## 4) Scoring Formula (starting point)
`total = 0.30*heat + 0.45*potential + 0.25*buildability`

Suggested normalization:
- Use percentile scaling per time window to avoid domination by giant projects.
- Apply recency decay for stale repositories.
- Add exploration boost for low-star but high-growth candidates.

## 5) Quality Bar Before Release
- All API endpoints have schema validation and error contracts.
- End-to-end run succeeds from fresh database.
- At least 20 core tests pass (unit + integration smoke).
- Reproducible setup from README in <=10 minutes.

## 6) Week-by-week Execution Plan
### Week 1
- Build collector and storage schema.
- Finish checkpoint and retry strategy.

### Week 2
- Implement scoring and baseline ranking output.
- Add CLI/API for topic-based analysis.

### Week 3
- Build minimal UI and sample report page.
- Add logging and metrics snapshot.

### Week 4
- Stabilization, tests, docs, Docker packaging.
- MVP handoff package and demo script.

## 7) Definition of Done (MVP)
- End user can select a domain and obtain ranked opportunities with rationale.
- Output includes score decomposition and confidence.
- Documentation clearly states limitations and next-step backlog.
