import asyncio

from app.services.insight import InsightEngine
from app.services.llm import extract_json_object
from app.services.sample_data import build_sample_repositories
from app.services.scorer import TrendScorer
from app.services.validator import validate_payload


def test_extract_json_object_from_markdown_fence() -> None:
    text = """Here is output:
```json
{"status":"ok","value":1}
```
"""
    payload = extract_json_object(text)
    assert payload == {"status": "ok", "value": 1}


def test_insight_engine_fallback_output_valid_without_llm_key() -> None:
    repo = TrendScorer.score(build_sample_repositories("ai"))[0]
    engine = InsightEngine()
    payload = asyncio.run(engine.build_opportunity(repo, "ai"))
    result = validate_payload(payload)
    assert result["valid"] is True
    assert payload["status"] == "ok"

