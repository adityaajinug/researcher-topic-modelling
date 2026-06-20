"""Extract unique author IDs and basic info from works_raw.jsonl."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AUTHORS_RAW_PATH, WORKS_RAW_PATH
from src.utils import logger


def extract_authors(
    works_path: Path = WORKS_RAW_PATH,
    out_path: Path = AUTHORS_RAW_PATH,
) -> pd.DataFrame:
    if not works_path.exists():
        raise FileNotFoundError(f"works_raw.jsonl not found: {works_path}")

    authors: dict[str, dict] = {}

    with open(works_path, encoding="utf-8") as f:
        for line in f:
            try:
                work = json.loads(line)
            except json.JSONDecodeError:
                continue
            for authorship in work.get("authorships", []):
                a = authorship.get("author", {})
                aid = a.get("id")
                if not aid:
                    continue
                if aid not in authors:
                    authors[aid] = {
                        "author_id": aid,
                        "display_name": a.get("display_name", ""),
                        "orcid": a.get("orcid", ""),
                        "article_count": 0,
                    }
                authors[aid]["article_count"] += 1

    df = pd.DataFrame(list(authors.values()))
    df = df.sort_values("article_count", ascending=False).reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(out_path, orient="records", lines=True, force_ascii=False)

    logger.info(
        "Extracted %d unique authors from %d works", len(df), sum(1 for _ in open(works_path))
    )
    return df


if __name__ == "__main__":
    extract_authors()
