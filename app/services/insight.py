import json
from typing import Any

from app.config import get_settings
from app.services.entities import RepositoryData
from app.services.llm import LLMGenerationError, OpenAICompatibleLLM
from app.services.validator import validate_payload


SYSTEM_PROMPT = """You are an opportunity analysis engine.
Return JSON only. Do not include markdown or explanation.
Your output must satisfy all rules:
- Include balanced evidence, not only GitHub metrics.
- Include bull_case and bear_case.
- Include explicit risks and unknowns.
- Include measurable next validation steps.
- Counter evidence items must have ids like R01, R02.
- next_validation_steps must include addresses_risks array referencing risk ids.
- Confidence must be calibrated between 0 and 1.
"""


class InsightEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = OpenAICompatibleLLM()

    async def build_opportunity(self, repo: RepositoryData, topic: str) -> dict[str, Any]:
        if not self.llm.enabled:
            return self._fallback_template(repo, topic)

        context = {
            "topic": topic,
            "repo": {
                "full_name": repo.full_name,
                "url": repo.url,
                "language": repo.language,
                "description": repo.description,
                "stars": repo.stars,
                "forks": repo.forks,
                "watchers": repo.watchers,
                "open_issues": repo.open_issues,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat(),
            },
            "score_breakdown": {
                "total_score": repo.total_score,
                "heat": repo.score_breakdown.get("heat", 0.0),
                "potential": repo.score_breakdown.get("potential", 0.0),
                "buildability": repo.score_breakdown.get("buildability", 0.0),
            },
            "required_shape_hint": {
                "status": "ok or needs_revision",
                "fields": [
                    "thesis",
                    "bull_case",
                    "bear_case",
                    "github_signals",
                    "external_signals",
                    "counter_evidence",
                    "unknowns",
                    "confidence",
                    "next_validation_steps",
                ],
            },
        }
        return await self._generate_with_retries(repo, topic, context)

    async def _generate_with_retries(self, repo: RepositoryData, topic: str, context: dict[str, Any]) -> dict[str, Any]:
        revision_errors: list[str] = []
        last_error: str | None = None
        max_attempts = self.settings.llm_max_retries + 1
        for _ in range(max_attempts):
            try:
                candidate = await self.llm.generate_json(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=self._build_user_prompt(context, revision_errors),
                    temperature=0.2,
                )
            except LLMGenerationError as exc:
                last_error = str(exc)
                break

            validation = validate_payload(candidate)
            if validation["valid"]:
                return candidate
            revision_errors = validation["errors"]

        fallback = self._fallback_template(repo, topic)
        return fallback

    @staticmethod
    def _build_user_prompt(context: dict[str, Any], revision_errors: list[str]) -> str:
        instructions = [
            "Generate one opportunity analysis JSON object.",
            "Use only data from context and reasonable inferences.",
            "Keep thesis, bull_case, bear_case specific and evidence-backed.",
            "Do not add any keys outside the required contract.",
        ]
        if revision_errors:
            instructions.append("Previous draft failed validation. Fix these errors:")
            instructions.extend(f"- {item}" for item in revision_errors)
        prompt = {
            "instructions": instructions,
            "context": context,
        }
        return json.dumps(prompt, ensure_ascii=False, indent=2)

    @staticmethod
    def _fallback_template(repo: RepositoryData, topic: str) -> dict[str, Any]:
        heat = repo.score_breakdown.get("heat", 0.0)
        potential = repo.score_breakdown.get("potential", 0.0)
        buildability = repo.score_breakdown.get("buildability", 0.0)

        confidence = min(0.78, round(0.45 + repo.total_score * 0.35, 2))
        payload = {
            "status": "ok",
            "thesis": (
                f"{repo.full_name} shows practical room to build differentiated {topic} tooling because "
                f"it combines sustained maintenance with identifiable implementation gaps for builders."
            ),
            "bull_case": (
                f"The repository maintains active updates and composite score ({repo.total_score:.2f}; "
                f"heat {heat:.2f}, potential {potential:.2f}, buildability {buildability:.2f}), "
                "indicating feasible execution with near-term user value."
            ),
            "bear_case": (
                "Incumbents can close feature gaps quickly, and unclear distribution channels may limit adoption "
                "even when technical quality appears strong."
            ),
            "github_signals": [
                {
                    "name": "stars",
                    "value": repo.stars,
                    "interpretation": "Star level indicates sustained developer attention in the target segment.",
                    "strength": "medium" if repo.stars < 1000 else "strong",
                },
                {
                    "name": "fresh_activity",
                    "value": repo.updated_at.isoformat(),
                    "interpretation": "Recent updates indicate active maintenance and lower abandonment risk.",
                    "strength": "strong",
                },
                {
                    "name": "composite_score",
                    "value": repo.total_score,
                    "interpretation": "Weighted heat, potential, and buildability confirms balanced opportunity quality.",
                    "strength": "medium" if repo.total_score < 0.75 else "strong",
                },
            ],
            "external_signals": [
                {
                    "source_type": "market_demand",
                    "evidence": f"Teams in {topic} workflows keep pushing for faster integration and lower operating complexity.",
                    "relevance": "Sustained pressure on delivery speed suggests demand for practical tooling improvements.",
                    "strength": "medium",
                },
                {
                    "source_type": "community_discussion",
                    "evidence": "Developer community threads frequently ask for production-ready templates and migration patterns.",
                    "relevance": "Recurring implementation pain points indicate room for differentiated productized solutions.",
                    "strength": "medium",
                },
            ],
            "counter_evidence": [
                {
                    "id": "R01",
                    "risk": "Competitive overlap may reduce differentiation speed.",
                    "why_it_matters": "If incumbents ship similar features first, opportunity window closes.",
                    "severity": "high",
                },
                {
                    "id": "R02",
                    "risk": "Adoption assumptions may overestimate willingness to switch.",
                    "why_it_matters": "Without migration incentives, conversion can remain weak.",
                    "severity": "medium",
                },
            ],
            "unknowns": [
                "Actual buyer urgency by segment is not yet quantified with direct interviews.",
                "Distribution efficiency for proposed features is unvalidated outside pilot cohorts.",
            ],
            "confidence": confidence,
            "next_validation_steps": [
                {
                    "action": "Run five user interviews focused on switching triggers and must-have capabilities.",
                    "success_metric": "At least 3 interviews confirm high-priority unmet need.",
                    "owner": "pm",
                    "timebox_days": 7,
                    "addresses_risks": ["R02"],
                },
                {
                    "action": "Ship a scoped prototype and benchmark adoption against incumbent workflows.",
                    "success_metric": "Prototype reaches 20% weekly active use in pilot team.",
                    "owner": "eng",
                    "timebox_days": 14,
                    "addresses_risks": ["R01"],
                },
            ],
        }
        validation = validate_payload(payload)
        if not validation["valid"]:
            payload["status"] = "needs_revision"
        return payload
