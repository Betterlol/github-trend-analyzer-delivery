import asyncio

from app.services.insight import InsightEngine
from app.services.sample_data import build_sample_repositories
from app.services.scorer import TrendScorer
from app.services.validator import validate_payload


def test_generated_opportunity_passes_validation() -> None:
    repo = TrendScorer.score(build_sample_repositories("data"))[0]
    payload = asyncio.run(InsightEngine().build_opportunity(repo, "data"))
    result = validate_payload(payload)
    assert result["valid"] is True
    assert result["status"] == "ok"
