import json
import os
from pathlib import Path
from urllib.request import urlretrieve

import faiss
import numpy as np


INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", "index.faiss"))
IDS_PATH = Path(os.getenv("FAISS_IDS_PATH", "index_ids.json"))
INDEX_URL = os.getenv("FAISS_INDEX_URL")
IDS_URL = os.getenv("FAISS_IDS_URL")


class RuntimeStore:
    def __init__(self, index, movie_ids, movie_vectors):
        self.index = index
        self.movie_ids = movie_ids
        self.movie_vectors = movie_vectors

    @classmethod
    def load(cls):
        cls._ensure_artifact(INDEX_PATH, INDEX_URL)
        cls._ensure_artifact(IDS_PATH, IDS_URL)

        if not INDEX_PATH.exists():
            raise RuntimeError(f"Missing required FAISS index: {INDEX_PATH}")

        if not IDS_PATH.exists():
            raise RuntimeError(f"Missing required index id map: {IDS_PATH}")

        index = faiss.read_index(str(INDEX_PATH))

        with IDS_PATH.open("r", encoding="utf-8") as file:
            movie_ids = json.load(file)

        if index.ntotal != len(movie_ids):
            raise RuntimeError(
                "FAISS index and index id map are out of sync: "
                f"index.ntotal={index.ntotal}, ids={len(movie_ids)}"
            )

        movie_vectors = {}

        for position, movie_id in enumerate(movie_ids):
            movie_vectors[movie_id] = np.array(
                index.reconstruct(position),
                dtype="float32",
            )

        return cls(index=index, movie_ids=movie_ids, movie_vectors=movie_vectors)

    @staticmethod
    def _ensure_artifact(path: Path, url: str | None):
        if path.exists():
            return

        if not url:
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(url, path)

    def search(self, query_vector, excluded_ids, top_k, search_k):
        if not self.movie_ids:
            return []

        norm = np.linalg.norm(query_vector)
        if norm == 0:
            return self.fallback(top_k=top_k, excluded_ids=excluded_ids)

        query_vector = query_vector.astype("float32") / norm
        _, indices = self.index.search(np.array([query_vector], dtype="float32"), search_k)

        recommendations = []

        for idx in indices[0]:
            if idx < 0 or idx >= len(self.movie_ids):
                continue

            movie_id = self.movie_ids[idx]
            if movie_id in excluded_ids or movie_id in recommendations:
                continue

            recommendations.append(movie_id)

            if len(recommendations) == top_k:
                break

        if len(recommendations) < top_k:
            recommendations.extend(
                self.fallback(
                    top_k=top_k - len(recommendations),
                    excluded_ids=excluded_ids.union(recommendations),
                )
            )

        return recommendations

    def fallback(self, top_k, excluded_ids=None):
        excluded_ids = excluded_ids or set()

        recommendations = []

        for movie_id in self.movie_ids:
            if movie_id in excluded_ids:
                continue

            recommendations.append(movie_id)

            if len(recommendations) == top_k:
                break

        return recommendations

    def recommend(self, seed_movie_ids, top_k, search_k):
        if not self.movie_ids:
            return []

        known_seed_ids = [movie_id for movie_id in seed_movie_ids if movie_id in self.movie_vectors]

        if not known_seed_ids:
            return self.fallback(top_k=top_k)

        vectors = [self.movie_vectors[movie_id] for movie_id in known_seed_ids]
        query_vector = np.mean(vectors, axis=0).astype("float32")

        return self.search(
            query_vector=query_vector,
            excluded_ids=set(known_seed_ids),
            top_k=top_k,
            search_k=search_k,
        )
