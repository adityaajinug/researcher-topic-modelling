from pathlib import Path

# Institution
INSTITUTION_ID = "I4210127958"  # Universitas Dian Nuswantoro — OpenAlex ID

# OpenAlex API
OPENALEX_BASE_URL = "https://api.openalex.org"
WORKS_FIELDS = "id,doi,title,publication_year,type,primary_location,authorships,abstract_inverted_index,cited_by_count"

# Topic modelling
TOPIC_K_MIN = 5
TOPIC_K_MAX = 20
MIN_ARTICLES_PER_AUTHOR = 5

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "outputs"

WORKS_RAW_PATH = RAW_DIR / "works_raw.jsonl"
AUTHORS_RAW_PATH = RAW_DIR / "authors_raw.jsonl"
SCIMAGO_PATH = RAW_DIR / "scimagojr.csv"
WORKS_FILTERED_PATH = INTERIM_DIR / "works_filtered.csv"
CORPUS_PATH = INTERIM_DIR / "corpus_per_author.csv"
TOPIC_DIST_PATH = PROCESSED_DIR / "topic_distribution.csv"
TCI_SCORES_PATH = PROCESSED_DIR / "tci_scores.csv"
TCI_RANKING_PATH = OUTPUT_DIR / "tci_ranking.csv"
