"""Train LDA on the full corpus and save per-document topic distribution."""

import ast
import sys
from pathlib import Path

import pandas as pd
from gensim import corpora
from gensim.models import CoherenceModel, LdaModel
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CORPUS_PATH, TOPIC_DIST_PATH, TOPIC_K_MAX, TOPIC_K_MIN
from src.utils import logger


def _parse_tokens(val) -> list[str]:
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return str(val).split()


def train_lda(
    corpus_path: Path = CORPUS_PATH,
    out_path: Path = TOPIC_DIST_PATH,
    k_min: int = TOPIC_K_MIN,
    k_max: int = TOPIC_K_MAX,
) -> tuple[LdaModel, int]:
    df = pd.read_csv(corpus_path, dtype=str)
    texts = [_parse_tokens(t) for t in df["clean_tokens"]]
    texts = [t for t in texts if t]

    dictionary = corpora.Dictionary(texts)
    dictionary.filter_extremes(no_below=2, no_above=0.95)
    bow_corpus = [dictionary.doc2bow(t) for t in texts]

    # Find optimal k by coherence
    logger.info("Evaluating coherence for k=%d..%d", k_min, k_max)
    coherence_scores: list[tuple[int, float]] = []
    for k in tqdm(range(k_min, k_max + 1), desc="Coherence search"):
        model = LdaModel(
            corpus=bow_corpus,
            id2word=dictionary,
            num_topics=k,
            passes=10,
            random_state=42,
            per_word_topics=False,
        )
        cm = CoherenceModel(model=model, texts=texts, dictionary=dictionary, coherence="c_v")
        coherence_scores.append((k, cm.get_coherence()))

    best_k, best_score = max(coherence_scores, key=lambda x: x[1])
    logger.info("Best k=%d (coherence=%.4f)", best_k, best_score)

    # Train final model
    lda = LdaModel(
        corpus=bow_corpus,
        id2word=dictionary,
        num_topics=best_k,
        passes=20,
        random_state=42,
    )

    # Save per-document topic distribution
    rows = []
    for i, bow in enumerate(bow_corpus):
        dist = dict(lda.get_document_topics(bow, minimum_probability=0.0))
        row = {f"topic_{t}": dist.get(t, 0.0) for t in range(best_k)}
        row["doc_index"] = i
        rows.append(row)

    df_dist = pd.DataFrame(rows)
    df_meta = df[["work_id", "author_id", "author_name"]].reset_index(drop=True)
    df_dist = pd.concat([df_meta, df_dist], axis=1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_dist.to_csv(out_path, index=False)
    logger.info("Topic distribution saved: %s (k=%d)", out_path, best_k)

    lda.save(str(out_path.parent / f"lda_k{best_k}.model"))
    return lda, best_k


if __name__ == "__main__":
    train_lda()
