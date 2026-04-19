from app.services.sample_data import build_sample_repositories
from app.services.scorer import TrendScorer


def test_trend_scorer_produces_sorted_scores() -> None:
    repos = build_sample_repositories("ai")
    ranked = TrendScorer.score(repos)

    assert len(ranked) == 3
    assert ranked[0].total_score >= ranked[1].total_score >= ranked[2].total_score
    for repo in ranked:
        assert 0.0 <= repo.total_score <= 1.0
        assert {"heat", "potential", "buildability"} <= set(repo.score_breakdown)

