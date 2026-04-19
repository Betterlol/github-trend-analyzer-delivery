import argparse
import asyncio
import json
from pathlib import Path

from app.db import Base, SessionLocal, engine
from app.services.pipeline import AnalysisPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub Trend Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Run topic analysis")
    analyze.add_argument("--topic", required=True, help="GitHub topic keyword")
    analyze.add_argument("--limit", type=int, default=20, help="Top N opportunities")
    analyze.add_argument("--offline", action="store_true", help="Use offline sample data")
    analyze.add_argument("--output", type=str, default="", help="Optional output JSON file path")
    return parser


async def run_analyze(topic: str, limit: int, offline: bool, output: str) -> int:
    Base.metadata.create_all(bind=engine)
    pipeline = AnalysisPipeline()
    with SessionLocal() as db:
        result = await pipeline.run(db=db, topic=topic, limit=limit, offline=offline)

    payload = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    print(payload)
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "analyze":
        return asyncio.run(run_analyze(args.topic, args.limit, args.offline, args.output))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

