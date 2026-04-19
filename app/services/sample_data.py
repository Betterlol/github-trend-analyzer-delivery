from datetime import UTC, datetime, timedelta

from app.services.entities import RepositoryData


def build_sample_repositories(topic: str) -> list[RepositoryData]:
    now = datetime.now(tz=UTC)
    return [
        RepositoryData(
            full_name=f"sample/{topic}-core",
            url=f"https://github.com/sample/{topic}-core",
            language="Python",
            description=f"{topic} core toolkit focused on production use cases.",
            created_at=now - timedelta(days=340),
            updated_at=now - timedelta(days=1),
            pushed_at=now - timedelta(hours=20),
            stars=780,
            forks=88,
            watchers=54,
            open_issues=19,
            topics=[topic, "tooling"],
        ),
        RepositoryData(
            full_name=f"sample/{topic}-ops",
            url=f"https://github.com/sample/{topic}-ops",
            language="Go",
            description=f"{topic} deployment and operations automation.",
            created_at=now - timedelta(days=540),
            updated_at=now - timedelta(days=2),
            pushed_at=now - timedelta(days=1),
            stars=430,
            forks=51,
            watchers=37,
            open_issues=11,
            topics=[topic, "devops"],
        ),
        RepositoryData(
            full_name=f"sample/{topic}-lab",
            url=f"https://github.com/sample/{topic}-lab",
            language="TypeScript",
            description=f"Experimental {topic} workflows and prototypes.",
            created_at=now - timedelta(days=170),
            updated_at=now - timedelta(days=1),
            pushed_at=now - timedelta(hours=12),
            stars=120,
            forks=18,
            watchers=15,
            open_issues=7,
            topics=[topic, "experimental"],
        ),
    ]

