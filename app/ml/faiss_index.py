"""Loading and validation for a read-only FAISS artifact release."""

from __future__ import annotations

from hashlib import sha256
import json
import logging
from pathlib import Path
from typing import Any

import faiss
import numpy as np


LOGGER = logging.getLogger(__name__)
MANIFEST_FILE = "manifest.json"
INDEX_FILE = "movie_index.bin"
MAP_FILE = "movie_index_map.json"
MANIFEST_SCHEMA_VERSION = 1


class ArtifactNotReadyError(Exception):
    """Raised when the configured artifact release cannot serve requests."""


class FaissIndex:
    """Read-only FAISS index loaded from one validated artifact release."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir.resolve()
        self.index = faiss.IndexFlatIP(0)
        self.id_map: list[str] = []
        self.manifest: dict[str, Any] | None = None
        self.unavailable_reason: str | None = None
        self._load()

    @property
    def is_ready(self) -> bool:
        return self.unavailable_reason is None and bool(self.id_map)

    @property
    def artifact_version(self) -> str | None:
        return self.manifest["artifact_version"] if self.manifest else None

    @property
    def movie_count(self) -> int:
        return len(self.id_map)

    def _load(self) -> None:
        try:
            manifest = self._read_manifest()
            self._validate_file_hashes(manifest)
            index = faiss.read_index(str(self.artifact_dir / INDEX_FILE))
            id_map = self._read_id_map()
            self._validate_contents(manifest, index, id_map)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self.unavailable_reason = str(exc)
            LOGGER.error("Recommendation artifact unavailable at %s: %s", self.artifact_dir, exc)
            return

        self.index = index
        self.id_map = id_map
        self.manifest = manifest
        LOGGER.info(
            "Loaded recommendation artifact version=%s movies=%d path=%s",
            self.artifact_version,
            self.movie_count,
            self.artifact_dir,
        )

    def _read_manifest(self) -> dict[str, Any]:
        manifest_path = self.artifact_dir / MANIFEST_FILE
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"artifact manifest is missing: {manifest_path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("artifact manifest is not valid JSON") from exc

        if not isinstance(manifest, dict):
            raise ValueError("artifact manifest must be a JSON object")
        if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
            raise ValueError("artifact manifest has an unsupported schema version")
        if not isinstance(manifest.get("artifact_version"), str) or not manifest["artifact_version"]:
            raise ValueError("artifact manifest has no artifact version")
        if not isinstance(manifest.get("files"), dict):
            raise ValueError("artifact manifest has no file hashes")
        return manifest

    def _validate_file_hashes(self, manifest: dict[str, Any]) -> None:
        expected_hashes = manifest["files"]
        for file_name in (INDEX_FILE, MAP_FILE):
            expected_hash = expected_hashes.get(file_name)
            if not isinstance(expected_hash, str):
                raise ValueError(f"artifact manifest has no hash for {file_name}")
            if _file_hash(self.artifact_dir / file_name) != expected_hash:
                raise ValueError(f"artifact hash mismatch for {file_name}")

    def _read_id_map(self) -> list[str]:
        try:
            id_map = json.loads((self.artifact_dir / MAP_FILE).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("movie index map is not valid JSON") from exc
        if not isinstance(id_map, list) or not all(isinstance(movie_id, str) and movie_id for movie_id in id_map):
            raise ValueError("movie index map must contain non-empty movie ids")
        if len(id_map) != len(set(id_map)):
            raise ValueError("movie index map contains duplicate movie ids")
        return id_map

    @staticmethod
    def _validate_contents(manifest: dict[str, Any], index, id_map: list[str]) -> None:
        if manifest.get("distance_metric") != "inner_product":
            raise ValueError("artifact manifest has an unsupported distance metric")
        if not isinstance(manifest.get("dimension"), int) or manifest["dimension"] <= 0:
            raise ValueError("artifact manifest has an invalid vector dimension")
        if not isinstance(manifest.get("movie_count"), int) or manifest["movie_count"] <= 0:
            raise ValueError("artifact manifest has an invalid movie count")
        if index.d != manifest["dimension"]:
            raise ValueError("FAISS index dimension does not match the manifest")
        if index.ntotal != len(id_map):
            raise ValueError("FAISS index vector count does not match the movie index map")
        if index.ntotal != manifest["movie_count"]:
            raise ValueError("FAISS index vector count does not match the manifest")

    def search(self, query_vector: np.ndarray, k: int = 10) -> list[str]:
        if not self.is_ready:
            return []
        query = np.asarray([query_vector], dtype="float32")
        _, indices = self.index.search(query, k)
        return [self.id_map[index] for index in indices[0] if 0 <= index < len(self.id_map)]


def _file_hash(path: Path) -> str:
    try:
        return sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError as exc:
        raise ValueError(f"artifact file is missing: {path.name}") from exc
