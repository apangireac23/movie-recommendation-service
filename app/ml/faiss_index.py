import faiss
import numpy as np
import json
import os

INDEX_PATH = "app/data/movie_index.bin"
MAP_PATH = "app/data/movie_index_map.json"

DIMENSION = 384


class FaissIndex:

    def __init__(self):
        self.index = self._load_index()
        self.id_map = self._load_id_map()

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

    def add_movie(self, movie_id, embedding):

        if movie_id in self.id_map:
            return

        vector = np.array([embedding]).astype("float32")

        self.index.add(vector)

        self.id_map.append(movie_id)

        self.save()

    def search(self, query_vector, k=10):

        if len(self.id_map) == 0:
            return []

        query = np.array([query_vector]).astype("float32")

        distances, indices = self.index.search(query, k)

        results = []

        for idx in indices[0]:
            if idx < len(self.id_map):
                results.append(self.id_map[idx])

        return results
    

    def save(self):
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

        faiss.write_index(self.index, INDEX_PATH)

        with open(MAP_PATH, "w") as f:
            json.dump(self.id_map, f)
