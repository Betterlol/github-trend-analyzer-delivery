from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import PipelineRun, Repo, RepoAnalysis, RepoMetric
from app.services.entities import RepositoryData


def upsert_repo(db: Session, repo_data: RepositoryData) -> Repo:
    repo = db.scalar(select(Repo).where(Repo.full_name == repo_data.full_name))
    if repo is None:
        repo = Repo(
            full_name=repo_data.full_name,
            url=repo_data.url,
            language=repo_data.language,
            created_at=repo_data.created_at,
            updated_at=repo_data.updated_at,
            stars=repo_data.stars,
            forks=repo_data.forks,
            watchers=repo_data.watchers,
        )
        db.add(repo)
        db.flush()
    else:
        repo.url = repo_data.url
        repo.language = repo_data.language
        repo.created_at = repo_data.created_at
        repo.updated_at = repo_data.updated_at
        repo.stars = repo_data.stars
        repo.forks = repo_data.forks
        repo.watchers = repo_data.watchers
        db.flush()
    return repo


def upsert_metrics(db: Session, repo_id: int, repo_data: RepositoryData) -> None:
    metric = db.scalar(select(RepoMetric).where(RepoMetric.repo_id == repo_id))
    commit_30d = max(1, min(120, int(repo_data.score_breakdown.get("heat", 0.0) * 100)))
    contributors_30d = max(1, min(25, int(repo_data.score_breakdown.get("buildability", 0.0) * 20)))
    releases_90d = max(0, min(12, int(repo_data.score_breakdown.get("potential", 0.0) * 10)))
    issue_close_rate = round(min(1.0, 1.0 - repo_data.open_issues / 200), 3)
    if metric is None:
        metric = RepoMetric(
            repo_id=repo_id,
            commit_30d=commit_30d,
            contributors_30d=contributors_30d,
            releases_90d=releases_90d,
            issue_close_rate=issue_close_rate,
        )
        db.add(metric)
    else:
        metric.commit_30d = commit_30d
        metric.contributors_30d = contributors_30d
        metric.releases_90d = releases_90d
        metric.issue_close_rate = issue_close_rate
    db.flush()


def insert_analysis(db: Session, repo_id: int, opportunity: dict[str, Any]) -> None:
    analysis = RepoAnalysis(
        repo_id=repo_id,
        category="opportunity",
        tags=",".join(opportunity.get("unknowns", [])[:2]),
        rationale=opportunity.get("thesis", ""),
        confidence=float(opportunity.get("confidence", 0.0)),
        analyzed_at=datetime.now(tz=UTC),
    )
    db.add(analysis)
    db.flush()


def insert_pipeline_run(db: Session, run_id: str, stage: str, status: str, duration_ms: int, error_message: str | None = None) -> None:
    db.add(
        PipelineRun(
            run_id=run_id,
            stage=stage,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            created_at=datetime.now(tz=UTC),
        )
    )
    db.flush()


def fetch_recent_runs(db: Session, limit: int = 10) -> list[PipelineRun]:
    stmt = select(PipelineRun).order_by(desc(PipelineRun.created_at)).limit(limit)
    return list(db.scalars(stmt))


def fetch_language_distribution(db: Session, limit: int = 8) -> list[tuple[str, int]]:
    language_field = func.coalesce(Repo.language, "Unknown")
    repo_count_col = func.count(Repo.id).label("repo_count")
    stmt = (
        select(language_field.label("language"), repo_count_col)
        .group_by(language_field)
        .order_by(desc(repo_count_col))
        .limit(limit)
    )
    return [(row.language, int(row.repo_count)) for row in db.execute(stmt)]


def fetch_recent_analyses(db: Session, limit: int = 10) -> list[tuple[str, float, datetime, str]]:
    stmt = (
        select(Repo.full_name, RepoAnalysis.confidence, RepoAnalysis.analyzed_at, RepoAnalysis.rationale)
        .join(Repo, Repo.id == RepoAnalysis.repo_id)
        .order_by(desc(RepoAnalysis.analyzed_at))
        .limit(limit)
    )
    return [(row.full_name, float(row.confidence), row.analyzed_at, row.rationale) for row in db.execute(stmt)]


def fetch_overall_counts(db: Session) -> tuple[int, int, int]:
    repo_count = int(db.scalar(select(func.count(Repo.id))) or 0)
    analysis_count = int(db.scalar(select(func.count(RepoAnalysis.id))) or 0)
    run_count = int(db.scalar(select(func.count(PipelineRun.run_id))) or 0)
    return repo_count, analysis_count, run_count
