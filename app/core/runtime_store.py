"""Read-only artifacts shared by the request handlers."""

import os
from pathlib import Path

from app.ml.faiss_index import FaissIndex

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "v1"
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", DEFAULT_ARTIFACT_DIR))

faiss_index = FaissIndex(ARTIFACT_DIR)
