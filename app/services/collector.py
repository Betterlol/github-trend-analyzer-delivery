from datetime import UTC, datetime

import httpx

from app.config import get_settings
from app.services.entities import RepositoryData


class CollectorError(RuntimeError):
    pass


def _parse_iso8601(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubCollector:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def collect(self, topic: str) -> list[RepositoryData]:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-trend-analyzer"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        collected: list[RepositoryData] = []
        async with httpx.AsyncClient(base_url=self.settings.github_api_base, timeout=self.settings.github_request_timeout_sec) as client:
            for page in range(1, self.settings.github_max_pages + 1):
                params = {
                    "q": f"topic:{topic}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": self.settings.github_per_page,
                    "page": page,
                }
                response = await client.get("/search/repositories", params=params, headers=headers)
                if response.status_code in (401, 403):
                    raise CollectorError(f"github auth/rate-limit error: {response.status_code}")
                if response.status_code >= 500:
                    raise CollectorError(f"github server error: {response.status_code}")
                if response.status_code != 200:
                    raise CollectorError(f"github api error: {response.status_code} {response.text}")

                payload = response.json()
                items = payload.get("items", [])
                if not items:
                    break
                collected.extend(self._map_item(item) for item in items)

        return collected

    @staticmethod
    def _map_item(item: dict) -> RepositoryData:
        return RepositoryData(
            full_name=item.get("full_name", ""),
            url=item.get("html_url", ""),
            language=item.get("language"),
            description=item.get("description") or "",
            created_at=_parse_iso8601(item.get("created_at")),
            updated_at=_parse_iso8601(item.get("updated_at")),
            pushed_at=_parse_iso8601(item.get("pushed_at")),
            stars=int(item.get("stargazers_count", 0)),
            forks=int(item.get("forks_count", 0)),
            watchers=int(item.get("watchers_count", 0)),
            open_issues=int(item.get("open_issues_count", 0)),
            topics=item.get("topics") or [],
        )

