"""Clean text, detect language, and tokenize with appropriate stopwords."""

import re
import sys
from pathlib import Path

import nltk
import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CORPUS_PATH
from src.utils import logger

DetectorFactory.seed = 42

# Download NLTK data on first run
for _pkg in ("stopwords", "punkt"):
    try:
        nltk.data.find(f"corpora/{_pkg}" if _pkg == "stopwords" else f"tokenizers/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

from nltk.corpus import stopwords  # noqa: E402
from nltk.tokenize import word_tokenize  # noqa: E402

EN_STOPWORDS = set(stopwords.words("english"))

try:
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

    _id_factory = StopWordRemoverFactory()
    ID_STOPWORDS = set(_id_factory.get_stop_words())
except ImportError:
    ID_STOPWORDS = set()
    logger.warning("Sastrawi not installed — Indonesian stopwords unavailable")


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str, lang: str) -> list[str]:
    stops = EN_STOPWORDS | (ID_STOPWORDS if lang == "id" else set())
    tokens = word_tokenize(text)
    return [t for t in tokens if len(t) > 2 and t not in stops]


def detect_lang(text: str) -> str:
    try:
        return detect(text[:500])
    except LangDetectException:
        return "en"


def preprocess_text(path: Path = CORPUS_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    tqdm.pandas(desc="Preprocessing")

    df["lang"] = df["full_text"].progress_apply(detect_lang)
    df["clean_text"] = df["full_text"].apply(_clean)
    df["clean_tokens"] = df.apply(
        lambda r: _tokenize(r["clean_text"], r["lang"]), axis=1
    )
    df["clean_tokens_str"] = df["clean_tokens"].apply(lambda t: " ".join(t))

    lang_counts = df["lang"].value_counts().to_dict()
    logger.info("Language distribution: %s", lang_counts)
    logger.info("Preprocessed %d documents", len(df))

    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    preprocess_text()
