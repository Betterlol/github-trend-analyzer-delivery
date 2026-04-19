import asyncio
import os
from uuid import uuid4

os.environ["DATABASE_URL"] = f"sqlite:////tmp/test_{uuid4().hex}.db"

from app.db import Base, SessionLocal, engine
from app.main import analyze, dashboard, health
from app.schemas import AnalyzeRequest


def test_health_handler() -> None:
    response = health()
    assert response.status == "ok"


def test_analyze_handler_offline() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        payload = AnalyzeRequest(topic="ml", limit=2, offline=True)
        response = asyncio.run(analyze(payload=payload, db=db))
    assert response.data_source == "offline_sample"
    assert response.total_candidates >= 2
    assert len(response.ranked_repos) == 2
    assert len(response.opportunities) == 2
    assert response.validation_summary["llm_mode"] in {"enabled", "fallback_template"}


def test_dashboard_handler_after_analysis() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        payload = AnalyzeRequest(topic="ml", limit=2, offline=True)
        _ = asyncio.run(analyze(payload=payload, db=db))
        snapshot = dashboard(db=db)
    assert snapshot.repo_count >= 2
    assert snapshot.analysis_count >= 2
    assert snapshot.run_count >= 1
    assert len(snapshot.recent_runs) >= 1
