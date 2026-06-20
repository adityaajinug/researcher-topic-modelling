"""Join works with Scimago journal tier data and filter to Q1/Q2 only."""

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SCIMAGO_PATH, WORKS_FILTERED_PATH, WORKS_RAW_PATH
from src.utils import logger


def _normalize_issn(issn: str | None) -> str:
    if not issn:
        return ""
    cleaned = re.sub(r"[^0-9Xx]", "", str(issn)).upper()
    if len(cleaned) == 8:
        return f"{cleaned[:4]}-{cleaned[4:]}"
    return issn


def load_scimago(path: Path = SCIMAGO_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df["issn_norm"] = df["Issn"].apply(_normalize_issn)
    return df[["issn_norm", "Title", "SJR Best Quartile"]].rename(
        columns={"Title": "journal_title", "SJR Best Quartile": "quartile"}
    )


def works_to_df(works_path: Path = WORKS_RAW_PATH) -> pd.DataFrame:
    rows = []
    with open(works_path, encoding="utf-8") as f:
        for line in f:
            try:
                w = json.loads(line)
            except json.JSONDecodeError:
                continue

            loc = w.get("primary_location") or {}
            source = loc.get("source") or {}
            issn_l = source.get("issn_l")
            issn_list = source.get("issn") or []
            issn_raw = issn_l or (issn_list[0] if issn_list else None)

            for auth in w.get("authorships", []):
                a = auth.get("author", {})
                rows.append(
                    {
                        "work_id": w.get("id"),
                        "doi": w.get("doi"),
                        "title": w.get("title"),
                        "publication_year": w.get("publication_year"),
                        "cited_by_count": w.get("cited_by_count"),
                        "abstract_inverted_index": json.dumps(
                            w.get("abstract_inverted_index") or {}
                        ),
                        "issn": _normalize_issn(issn_raw),
                        "author_id": a.get("id"),
                        "author_name": a.get("display_name"),
                    }
                )

    return pd.DataFrame(rows)


def join_scimago(
    works_path: Path = WORKS_RAW_PATH,
    scimago_path: Path = SCIMAGO_PATH,
    out_path: Path = WORKS_FILTERED_PATH,
) -> pd.DataFrame:
    df_works = works_to_df(works_path)
    df_sjr = load_scimago(scimago_path)

    df = df_works.merge(df_sjr, left_on="issn", right_on="issn_norm", how="left")

    before = len(df["work_id"].unique())
    df = df[df["quartile"].isin(["Q1", "Q2"])]
    after = len(df["work_id"].unique())
    logger.info(
        "Scimago filter: %d → %d unique works (dropped %d non-Q1/Q2)", before, after, before - after
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info("Saved filtered works to %s", out_path)
    return df


if __name__ == "__main__":
    join_scimago()
