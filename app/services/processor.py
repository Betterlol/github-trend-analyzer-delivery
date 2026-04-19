from app.services.entities import RepositoryData


class RepoProcessor:
    @staticmethod
    def normalize(repos: list[RepositoryData]) -> list[RepositoryData]:
        deduped: dict[str, RepositoryData] = {}
        for repo in repos:
            if not repo.full_name or not repo.url:
                continue
            existing = deduped.get(repo.full_name)
            if existing is None or repo.updated_at > existing.updated_at:
                deduped[repo.full_name] = repo
        return list(deduped.values())

