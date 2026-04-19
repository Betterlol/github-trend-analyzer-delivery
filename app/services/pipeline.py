import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.collector import CollectorError, GitHubCollector
from app.services.insight import InsightEngine
from app.services.processor import RepoProcessor
from app.services.sample_data import build_sample_repositories
from app.services.scorer import TrendScorer
from app.services.storage import insert_analysis, insert_pipeline_run, upsert_metrics, upsert_repo
from app.services.validator import validate_payload


class AnalysisPipeline:
    def __init__(self) -> None:
        self.collector = GitHubCollector()
        self.processor = RepoProcessor()
        self.scorer = TrendScorer()
        self.insight_engine = InsightEngine()

    async def run(self, db: Session, topic: str, limit: int = 20, offline: bool = False) -> dict[str, Any]:
        run_id = uuid.uuid4().hex[:12]
        started = datetime.now(tz=UTC)
        status = "success"
        error_message: str | None = None
        data_source = "offline_sample" if offline else "github_api"
        source_detail: str | None = None
        llm_mode = "enabled" if self.insight_engine.llm.enabled else "fallback_template"

        try:
            if offline:
                repos = build_sample_repositories(topic)
            else:
                try:
                    repos = await self.collector.collect(topic)
                    if not repos:
                        repos = build_sample_repositories(topic)
                        data_source = "sample_fallback"
                        source_detail = "github API returned empty result set"
                except CollectorError as exc:
                    repos = build_sample_repositories(topic)
                    data_source = "sample_fallback"
                    source_detail = f"github API error, fallback sample used: {exc}"

            normalized = self.processor.normalize(repos)
            ranked = self.scorer.score(normalized)[:limit]

            opportunities: list[dict[str, Any]] = []
            validation_errors = 0
            for repo in ranked:
                repo_row = upsert_repo(db, repo)
                upsert_metrics(db, repo_row.id, repo)
                opp = await self.insight_engine.build_opportunity(repo, topic)
                validation = validate_payload(opp)
                if not validation["valid"]:
                    validation_errors += 1
                opportunities.append(opp)
                insert_analysis(db, repo_row.id, opp)

            elapsed = int((datetime.now(tz=UTC) - started).total_seconds() * 1000)
            insert_pipeline_run(db, run_id, "analysis", status, elapsed)
            db.commit()

            ranked_repos = [
                {
                    "full_name": repo.full_name,
                    "url": repo.url,
                    "language": repo.language,
                    "stars": repo.stars,
                    "forks": repo.forks,
                    "watchers": repo.watchers,
                    "total_score": repo.total_score,
                    "heat": repo.score_breakdown.get("heat", 0.0),
                    "potential": repo.score_breakdown.get("potential", 0.0),
                    "buildability": repo.score_breakdown.get("buildability", 0.0),
                    "updated_at": repo.updated_at,
                }
                for repo in ranked
            ]
            return {
                "run_id": run_id,
                "data_source": data_source,
                "source_detail": source_detail,
                "total_candidates": len(normalized),
                "ranked_repos": ranked_repos,
                "opportunities": opportunities,
                "validation_summary": {
                    "valid_count": len(opportunities) - validation_errors,
                    "invalid_count": validation_errors,
                    "llm_mode": llm_mode,
                },
            }
        except Exception as exc:
            db.rollback()
            status = "failed"
            error_message = str(exc)
            elapsed = int((datetime.now(tz=UTC) - started).total_seconds() * 1000)
            insert_pipeline_run(db, run_id, "analysis", status, elapsed, error_message=error_message)
            db.commit()
            raise
