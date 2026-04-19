from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class RepositoryData:
    full_name: str
    url: str
    language: str | None
    description: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    stars: int
    forks: int
    watchers: int
    open_issues: int
    topics: list[str]
    score_breakdown: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0

