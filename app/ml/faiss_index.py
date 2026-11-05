import json
import os

import faiss
import numpy as np

INDEX_PATH = "app/data/movie_index.bin"
MAP_PATH = "app/data/movie_index_map.json"

DIMENSION = 384


class FaissIndex:
    """Read-only view of the offline-generated recommendation artifacts."""

    def __init__(self):
        self.index = self._load_index()
        self.id_map = self._load_id_map()
        if self.index.ntotal != len(self.id_map):
            # An incomplete artifact pair must never produce incorrectly
            # associated movie ids. Treat it as unavailable instead.
            self.index = faiss.IndexFlatIP(DIMENSION)
            self.id_map = []

    def _load_index(self):
        if not os.path.exists(INDEX_PATH) or os.path.getsize(INDEX_PATH) == 0:
            # return faiss.IndexFlatIP(DIMENSION)
            return faiss.IndexFlatIP(DIMENSION)

        try:
            return faiss.read_index(INDEX_PATH)
        except RuntimeError:
            # return faiss.IndexFlatL2(DIMENSION)
            return faiss.IndexFlatIP(DIMENSION)

    def _load_id_map(self):
        if not os.path.exists(MAP_PATH) or os.path.getsize(MAP_PATH) == 0:
            return []

        try:
            with open(MAP_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def search(self, query_vector, k=10):

        if len(self.id_map) == 0:
            return []

        query = np.array([query_vector]).astype("float32")

        distances, indices = self.index.search(query, k)

        results = []

        for idx in indices[0]:
            if 0 <= idx < len(self.id_map):
                results.append(self.id_map[idx])

        return results


class ArtifactNotReadyError(Exception):
    """Raised when the offline-generated artifacts cannot be used."""
