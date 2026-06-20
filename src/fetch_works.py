"""Pull journal-article works from OpenAlex for UDINUS institution, paginated via cursor."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import INSTITUTION_ID, OPENALEX_BASE_URL, WORKS_FIELDS, WORKS_RAW_PATH
from src.utils import get_session, logger, polite_delay

load_dotenv()


def fetch_works(out_path: Path = WORKS_RAW_PATH) -> int:
    api_key = os.getenv("OPENALEX_API_KEY", "")
    mailto = os.getenv("OPENALEX_MAILTO", "")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect already-fetched IDs for idempotent resume
    fetched_ids: set[str] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    fetched_ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        logger.info("Resume: %d works already in %s", len(fetched_ids), out_path)

    session = get_session()
    params: dict = {
        "filter": f"institutions.id:{INSTITUTION_ID},type:journal-article,has_doi:true",
        "select": WORKS_FIELDS,
        "per-page": 200,
        "cursor": "*",
        "mailto": mailto,
    }
    if api_key:
        params["api_key"] = api_key

    total_new = 0
    pbar = tqdm(desc="Fetching works", unit=" pages")

    with open(out_path, "a", encoding="utf-8") as fout:
        while True:
            resp = session.get(f"{OPENALEX_BASE_URL}/works", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            for work in results:
                wid = work.get("id", "")
                if wid not in fetched_ids:
                    fout.write(json.dumps(work, ensure_ascii=False) + "\n")
                    fetched_ids.add(wid)
                    total_new += 1

            pbar.update(1)
            pbar.set_postfix(new=total_new)

            next_cursor = data.get("meta", {}).get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor
            polite_delay()

    pbar.close()
    logger.info("Fetched %d new works. Total in file: %d", total_new, len(fetched_ids))
    return total_new


if __name__ == "__main__":
    fetch_works()
