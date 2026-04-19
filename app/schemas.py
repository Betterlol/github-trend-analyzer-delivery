from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=50)
    limit: int = Field(default=20, ge=1, le=50)
    offline: bool = Field(default=False, description="Use local sample data only")


class RankedRepo(BaseModel):
    full_name: str
    url: str
    language: str | None = None
    stars: int
    forks: int
    watchers: int
    total_score: float
    heat: float
    potential: float
    buildability: float
    updated_at: datetime


class AnalyzeResponse(BaseModel):
    run_id: str
    data_source: str
    source_detail: str | None = None
    total_candidates: int
    ranked_repos: list[RankedRepo]
    opportunities: list[dict[str, Any]]
    validation_summary: dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"


class RecentRun(BaseModel):
    run_id: str
    stage: str
    status: str
    duration_ms: int
    created_at: datetime
    error_message: str | None = None


class LanguageShare(BaseModel):
    language: str
    repo_count: int


class RecentAnalysis(BaseModel):
    repo_full_name: str
    confidence: float
    analyzed_at: datetime
    rationale: str


class DashboardResponse(BaseModel):
    repo_count: int
    analysis_count: int
    run_count: int
    recent_runs: list[RecentRun]
    language_distribution: list[LanguageShare]
    recent_analyses: list[RecentAnalysis]
