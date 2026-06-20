"""Orchestrator — runs all pipeline steps in order."""

import sys
from pathlib import Path

from src.compute_tci import compute_tci
from src.extract_authors import extract_authors
from src.fetch_works import fetch_works
from src.join_scimago import join_scimago
from src.preprocess_text import preprocess_text
from src.reconstruct_abstract import reconstruct_abstract
from src.topic_model import train_lda
from src.utils import logger
from src.verify_doi import verify_doi

BASE = Path(__file__).parent


def main():
    logger.info("=== Step 1: Fetch works from OpenAlex ===")
    fetch_works()

    logger.info("=== Step 2: Extract unique authors ===")
    extract_authors()

    logger.info("=== Step 3: Join Scimago — filter Q1/Q2 ===")
    join_scimago()

    logger.info("=== Step 4: Verify DOI activity ===")
    verify_doi()

    logger.info("=== Step 5: Reconstruct abstracts & build corpus ===")
    reconstruct_abstract()

    logger.info("=== Step 6: Preprocess text ===")
    preprocess_text()

    logger.info("=== Step 7: Train LDA topic model ===")
    train_lda()

    logger.info("=== Step 8: Compute TCI scores ===")
    df = compute_tci()

    logger.info("=== Pipeline complete ===")
    logger.info("TCI ranking saved. Top 5:")
    print(df[["author_name", "article_count", "tci"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
