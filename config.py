from pathlib import Path


SUBSET_JSON_PATH = Path("subset.json")
QUESTIONS_JSON_PATH = Path("questions.json")
META_INFO_JSON_PATH = Path("meta_info.json")
MD_FILES_PATH = Path("md")
PDF_FILES_PATH = Path("pdf")

MODEL_MINI = 'gpt-4o-mini-2024-07-18'
MODEL_BIG = 'gpt-4o-2024-08-06'
MODEL_REASONING = 'o3-mini-2025-01-31'

NUM_QUERY_EXPANSION_WORKERS = 100
NUM_SEARCH_WORKERS = 100
NUM_ANSWER_WORKERS = 100
