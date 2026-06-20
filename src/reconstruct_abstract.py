"""Decode abstract_inverted_index -> plain text, then build full_text = title + abstract."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CORPUS_PATH, WORKS_FILTERED_PATH
from src.utils import logger


def invert_index(index: dict) -> str:
    if not index:
        return ""
    max_pos = max(pos for positions in index.values() for pos in positions)
    tokens = [""] * (max_pos + 1)
    for word, positions in index.items():
        for pos in positions:
            tokens[pos] = word
    return " ".join(t for t in tokens if t)


def reconstruct_abstract(
    in_path: Path = WORKS_FILTERED_PATH,
    out_path: Path = CORPUS_PATH,
) -> pd.DataFrame:
    df = pd.read_csv(in_path, dtype=str)

    def decode(row):
        try:
            idx = json.loads(row.get("abstract_inverted_index") or "{}")
        except (json.JSONDecodeError, TypeError):
            idx = {}
        abstract = invert_index(idx)
        title = row.get("title") or ""
        return f"{title} {abstract}".strip()

    df["full_text"] = df.apply(decode, axis=1)

    # Build corpus: one row per (author, work) with full_text
    cols = ["work_id", "doi", "author_id", "author_name", "publication_year", "full_text"]
    df_corpus = df[[c for c in cols if c in df.columns]].copy()
    df_corpus = df_corpus[df_corpus["full_text"].str.len() > 10]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_corpus.to_csv(out_path, index=False)
    logger.info("Corpus saved: %d rows → %s", len(df_corpus), out_path)
    return df_corpus


if __name__ == "__main__":
    reconstruct_abstract()
