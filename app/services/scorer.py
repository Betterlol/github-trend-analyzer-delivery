from datetime import UTC, datetime

from app.services.entities import RepositoryData


def _percentiles(values: list[int]) -> dict[int, float]:
    if not values:
        return {}
    ordered = sorted(values)
    size = len(ordered)
    result: dict[int, float] = {}
    for index, value in enumerate(ordered):
        if size == 1:
            result[value] = 1.0
        else:
            result[value] = index / (size - 1)
    return result


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class TrendScorer:
    @staticmethod
    def score(repos: list[RepositoryData]) -> list[RepositoryData]:
        if not repos:
            return repos

        star_p = _percentiles([repo.stars for repo in repos])
        fork_p = _percentiles([repo.forks for repo in repos])
        watcher_p = _percentiles([repo.watchers for repo in repos])
        now = datetime.now(tz=UTC)

        for repo in repos:
            stars = star_p.get(repo.stars, 0.0)
            forks = fork_p.get(repo.forks, 0.0)
            watchers = watcher_p.get(repo.watchers, 0.0)

            heat = 0.5 * stars + 0.3 * forks + 0.2 * watchers

            days_since_push = max((now - repo.pushed_at).days, 0)
            recency = _clamp(1.0 - days_since_push / 365.0)
            momentum = _clamp(0.6 * recency + 0.4 * heat)
            exploration_boost = 1.0 if stars < 0.45 and recency > 0.75 else 0.45
            potential = 0.45 * recency + 0.35 * momentum + 0.20 * exploration_boost

            issue_pressure = _clamp(1.0 - repo.open_issues / 200.0)
            documentation_hint = 1.0 if repo.description else 0.4
            buildability = 0.45 * recency + 0.35 * issue_pressure + 0.20 * documentation_hint

            total = 0.30 * heat + 0.45 * potential + 0.25 * buildability
            repo.score_breakdown = {
                "heat": round(heat, 4),
                "potential": round(potential, 4),
                "buildability": round(buildability, 4),
            }
            repo.total_score = round(_clamp(total), 4)

        return sorted(repos, key=lambda repo: repo.total_score, reverse=True)

