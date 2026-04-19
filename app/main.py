from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.schemas import AnalyzeRequest, AnalyzeResponse, DashboardResponse, HealthResponse
from app.services.pipeline import AnalysisPipeline
from app.services.storage import fetch_language_distribution, fetch_overall_counts, fetch_recent_analyses, fetch_recent_runs


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="GitHub Trend Analyzer", version="0.1.0", lifespan=lifespan)
pipeline = AnalysisPipeline()
web_dir = Path(__file__).resolve().parents[1] / "web"
app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    repo_count, analysis_count, run_count = fetch_overall_counts(db)
    recent_runs = fetch_recent_runs(db, limit=10)
    language_distribution = fetch_language_distribution(db, limit=8)
    recent_analyses = fetch_recent_analyses(db, limit=10)
    return DashboardResponse(
        repo_count=repo_count,
        analysis_count=analysis_count,
        run_count=run_count,
        recent_runs=[
            {
                "run_id": item.run_id,
                "stage": item.stage,
                "status": item.status,
                "duration_ms": item.duration_ms,
                "created_at": item.created_at,
                "error_message": item.error_message,
            }
            for item in recent_runs
        ],
        language_distribution=[{"language": language, "repo_count": count} for language, count in language_distribution],
        recent_analyses=[
            {
                "repo_full_name": repo_name,
                "confidence": confidence,
                "analyzed_at": analyzed_at,
                "rationale": rationale,
            }
            for repo_name, confidence, analyzed_at, rationale in recent_analyses
        ],
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    result = await pipeline.run(db=db, topic=payload.topic, limit=payload.limit, offline=payload.offline)
    return AnalyzeResponse(**result)
