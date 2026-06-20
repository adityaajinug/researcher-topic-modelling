"""Verify that each DOI resolves (HEAD request to doi.org). Adds doi_active column."""

import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import WORKS_FILTERED_PATH
from src.utils import get_session, logger, polite_delay

DOI_BASE = "https://doi.org/"


def check_doi(session, doi: str) -> bool:
    if not doi:
        return False
    url = doi if doi.startswith("http") else DOI_BASE + doi.lstrip("/")
    try:
        resp = session.head(url, timeout=10, allow_redirects=True)
        return resp.status_code < 400
    except Exception:
        return False


def verify_doi(path: Path = WORKS_FILTERED_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)

    if "doi_active" in df.columns:
        pending = df["doi_active"].isna()
        logger.info("Resume: %d DOIs already checked, %d pending", (~pending).sum(), pending.sum())
    else:
        df["doi_active"] = None
        pending = pd.Series([True] * len(df))

    session = get_session(retries=3, backoff_factor=0.5)

    for idx in tqdm(df[pending].index, desc="Verifying DOIs"):
        doi = df.at[idx, "doi"]
        df.at[idx, "doi_active"] = check_doi(session, doi)
        polite_delay(0.1)

    before = len(df)
    df = df[df["doi_active"].astype(str) == "True"]
    logger.info(
        "DOI verification: %d → %d works (dropped %d inactive)", before, len(df), before - len(df)
    )

    df.to_csv(path, index=False)
    logger.info("Updated %s with doi_active column", path)
    return df


if __name__ == "__main__":
    verify_doi()
