"""Build a versioned FAISS recommendation artifact from a movie catalogue CSV.

This script is an offline tool. The running API never imports or executes it.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from pathlib import Path
import shutil
import sys
import tempfile

import faiss
import numpy as np


LOGGER = logging.getLogger(__name__)
REQUIRED_COLUMNS = {"id", "title", "overview"}
DEFAULT_MODEL = "all-MiniLM-L6-v2"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only FAISS artifact release from a movie catalogue CSV."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("catalogue/movies.csv"),
        help="Catalogue CSV containing id, title, and overview columns.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts"),
        help="Directory containing versioned artifact releases.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="New artifact version, such as v1 or 2026-11-05.",
    )
    parser.add_argument("--id-prefix", default="tmdb_", help="Prefix added to each source id.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Sentence Transformers model name.")
    parser.add_argument("--batch-size", type=int, default=256, help="Embedding batch size.")
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow downloading the embedding model when it is not cached locally.",
    )
    return parser.parse_args()


def validate_version(version: str) -> None:
    if not version or any(character in version for character in "\\/:"):
        raise ValueError("version must be a non-empty directory name without \\, /, or :")


def read_catalogue(source: Path, id_prefix: str) -> tuple[list[str], list[str]]:
    if not source.is_file():
        raise ValueError(f"catalogue CSV not found: {source}")

    with source.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("catalogue CSV has no header row")
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(f"catalogue CSV is missing columns: {', '.join(sorted(missing_columns))}")

        movie_ids: list[str] = []
        texts: list[str] = []
        seen_ids: set[str] = set()
        skipped_rows = 0

        for row_number, row in enumerate(reader, start=2):
            raw_id = (row["id"] or "").strip()
            title = (row["title"] or "").strip()
            overview = (row["overview"] or "").strip()
            if not raw_id:
                raise ValueError(f"catalogue CSV row {row_number} has no id")

            movie_id = f"{id_prefix}{raw_id}"
            if movie_id in seen_ids:
                raise ValueError(f"catalogue CSV contains duplicate id: {movie_id}")
            seen_ids.add(movie_id)

            if not title or not overview:
                skipped_rows += 1
                continue

            movie_ids.append(movie_id)
            texts.append(f"{title}\n{overview}")

    if not movie_ids:
        raise ValueError("catalogue CSV contains no movies with a title and overview")

    LOGGER.info("Read %d eligible movies; skipped %d incomplete rows", len(movie_ids), skipped_rows)
    return movie_ids, texts


def load_model(model_name: str, allow_download: bool):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "offline dependencies are missing; install requirements-offline.txt before building"
        ) from exc

    try:
        return SentenceTransformer(model_name, local_files_only=not allow_download)
    except Exception as exc:
        download_hint = " Run again with --allow-download if network access is intended."
        raise RuntimeError(f"could not load embedding model {model_name}.{download_hint}") from exc


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as artifact_file:
        for chunk in iter(lambda: artifact_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_release(
    output_root: Path,
    version: str,
    source: Path,
    model_name: str,
    movie_ids: list[str],
    embeddings: np.ndarray,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / version
    if target.exists():
        raise ValueError(f"artifact version already exists: {target}")

    with tempfile.TemporaryDirectory(prefix=f".{version}-", dir=output_root) as temporary_directory:
        release = Path(temporary_directory)
        index_path = release / "movie_index.bin"
        map_path = release / "movie_index_map.json"
        manifest_path = release / "manifest.json"

        index = faiss.IndexFlatIP(int(embeddings.shape[1]))
        index.add(embeddings.astype("float32"))
        faiss.write_index(index, str(index_path))
        map_path.write_text(json.dumps(movie_ids, separators=(",", ":")), encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "artifact_version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": {"path": str(source), "sha256": file_hash(source)},
            "embedding_model": model_name,
            "distance_metric": "inner_product",
            "dimension": int(embeddings.shape[1]),
            "movie_count": len(movie_ids),
            "files": {
                "movie_index.bin": file_hash(index_path),
                "movie_index_map.json": file_hash(map_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        reloaded_index = faiss.read_index(str(index_path))
        reloaded_ids = json.loads(map_path.read_text(encoding="utf-8"))
        if reloaded_index.ntotal != len(movie_ids) or reloaded_ids != movie_ids:
            raise RuntimeError("artifact validation failed after writing the release")

        shutil.move(str(release), str(target))

    return target


def main() -> int:
    arguments = parse_arguments()
    try:
        validate_version(arguments.version)
        movie_ids, texts = read_catalogue(arguments.source, arguments.id_prefix)
        model = load_model(arguments.model, arguments.allow_download)
        embeddings = model.encode(
            texts,
            batch_size=arguments.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        release = write_release(
            arguments.output_root,
            arguments.version,
            arguments.source,
            arguments.model,
            movie_ids,
            embeddings,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        LOGGER.error("Artifact build failed: %s", exc)
        return 1

    LOGGER.info("Built artifact version %s with %d movies at %s", arguments.version, len(movie_ids), release)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(main())
