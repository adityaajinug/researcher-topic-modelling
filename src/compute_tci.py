"""Compute Topic Consistency Index (TCI) per author using Shannon entropy."""

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MIN_ARTICLES_PER_AUTHOR, TCI_RANKING_PATH, TCI_SCORES_PATH, TOPIC_DIST_PATH
from src.utils import logger


def shannon_entropy(dist: list[float]) -> float:
    return -sum(p * math.log2(p) for p in dist if p > 0)


def compute_tci(
    dist_path: Path = TOPIC_DIST_PATH,
    tci_path: Path = TCI_SCORES_PATH,
    ranking_path: Path = TCI_RANKING_PATH,
    min_articles: int = MIN_ARTICLES_PER_AUTHOR,
) -> pd.DataFrame:
    df = pd.read_csv(dist_path)
    topic_cols = [c for c in df.columns if c.startswith("topic_")]
    num_topics = len(topic_cols)

    if num_topics == 0:
        raise ValueError("No topic_* columns found in topic distribution file.")

    h_max = math.log2(num_topics)

    # Filter authors with enough articles
    author_counts = df.groupby("author_id")["work_id"].nunique()
    eligible = author_counts[author_counts >= min_articles].index
    df = df[df["author_id"].isin(eligible)]
    logger.info(
        "Authors with ≥%d articles: %d (dropped %d)",
        min_articles,
        len(eligible),
        author_counts.shape[0] - len(eligible),
    )

    # Aggregate topic distribution per author (mean, then renormalize)
    agg = df.groupby(["author_id", "author_name"])[topic_cols].mean().reset_index()

    rows = []
    for _, row in agg.iterrows():
        dist = row[topic_cols].values.tolist()
        total = sum(dist)
        dist_norm = [p / total for p in dist] if total > 0 else dist
        h = shannon_entropy(dist_norm)
        tci = 1 - (h / h_max) if h_max > 0 else 0.0
        rows.append(
            {
                "author_id": row["author_id"],
                "author_name": row["author_name"],
                "article_count": author_counts[row["author_id"]],
                "entropy": round(h, 6),
                "tci": round(tci, 6),
                **{t: round(row[t], 6) for t in topic_cols},
            }
        )

    df_tci = pd.DataFrame(rows).sort_values("tci", ascending=False).reset_index(drop=True)

    tci_path.parent.mkdir(parents=True, exist_ok=True)
    df_tci.to_csv(tci_path, index=False)

    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    df_tci[["author_id", "author_name", "article_count", "entropy", "tci"]].to_csv(
        ranking_path, index=False
    )

    logger.info("TCI computed for %d authors. Top scorer: %s (%.4f)",
                len(df_tci),
                df_tci.iloc[0]["author_name"] if len(df_tci) else "N/A",
                df_tci.iloc[0]["tci"] if len(df_tci) else 0.0)
    return df_tci


if __name__ == "__main__":
    compute_tci()
