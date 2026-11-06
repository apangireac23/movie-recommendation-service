import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import faiss
import numpy as np

from app.ml.faiss_index import FaissIndex
from scripts.build_artifacts import read_catalogue

TEST_TEMP_ROOT = Path(__file__).parent / ".tmp"


def temporary_directory():
    TEST_TEMP_ROOT.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)


class ArtifactLoaderTests(unittest.TestCase):
    def _write_release(self, directory: Path) -> None:
        index_path = directory / "movie_index.bin"
        map_path = directory / "movie_index_map.json"
        index = faiss.IndexFlatIP(2)
        index.add(np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32"))
        faiss.write_index(index, str(index_path))
        map_path.write_text(json.dumps(["movie-1", "movie-2"]), encoding="utf-8")
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "artifact_version": "test-v1",
                    "distance_metric": "inner_product",
                    "dimension": 2,
                    "movie_count": 2,
                    "files": {
                        "movie_index.bin": digest(index_path),
                        "movie_index_map.json": digest(map_path),
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_loads_valid_complete_release(self):
        with temporary_directory() as temporary_path:
            release = Path(temporary_path)
            self._write_release(release)
            artifact = FaissIndex(release)

            self.assertTrue(artifact.is_ready)
            self.assertEqual(artifact.artifact_version, "test-v1")
            self.assertEqual(artifact.search(np.array([1.0, 0.0]), 1), ["movie-1"])

    def test_rejects_tampered_map(self):
        with temporary_directory() as temporary_path:
            release = Path(temporary_path)
            self._write_release(release)
            (release / "movie_index_map.json").write_text("[]", encoding="utf-8")

            artifact = FaissIndex(release)

            self.assertFalse(artifact.is_ready)
            self.assertIn("hash mismatch", artifact.unavailable_reason)


class CatalogueValidationTests(unittest.TestCase):
    def test_rejects_excessive_incomplete_rows(self):
        with temporary_directory() as temporary_path:
            source = Path(temporary_path) / "movies.csv"
            source.write_text(
                "id,title,overview\n1,Movie one,Valid overview\n2,Movie two,\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "exceeding"):
                read_catalogue(source, "tmdb_", max_skipped_fraction=0.1)

    def test_rejects_missing_required_column(self):
        with temporary_directory() as temporary_path:
            source = Path(temporary_path) / "movies.csv"
            source.write_text("id,title\n1,Movie one\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing columns"):
                read_catalogue(source, "tmdb_", max_skipped_fraction=0.1)
