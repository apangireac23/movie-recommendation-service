import pandas as pd

from app.core.database import SessionLocal
from app.ml.embedding_model import _get_model
from app.ml.faiss_index import FaissIndex
from app.repositories.movie_repository import MovieRepository

BATCH_SIZE = 16
LIMIT = 5000  # start small

model = _get_model()

def clean_row(row):
    if pd.isna(row["overview"]) or len(row["overview"]) < 30:
        return None

    return {
        "id": f"tmdb_{row['id']}",
        "title": row["title"],
        "plot": row["overview"],
        "genre": None
    }


def main():
    df = pd.read_csv("tmdb_5000_movies.csv")


    # clean + filter
    data = []
    for _, row in df.iterrows():
        item = clean_row(row)
        if item:
            data.append(item)

    data = data[:LIMIT]

    print(f"Total cleaned movies: {len(data)}")

    db = SessionLocal()
    faiss_index = FaissIndex()

    for i in range(0, len(data), BATCH_SIZE):

        batch = data[i:i+BATCH_SIZE]
        plots = [item["plot"] for item in batch]

        embeddings = model.encode(
            plots,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True
        )

        for j in range(len(batch)):

            movie_data = batch[j]
            embedding = embeddings[j]

            # ✅ DB FIRST (critical)
            MovieRepository.upsert_movie_with_embedding(
                db,
                movie_data,
                embedding.tolist()
            )

            # ✅ THEN FAISS
            faiss_index.add_movie(movie_data["id"], embedding)

        print(f"Processed batch {i} → {i + len(batch)}")

    # ✅ Save FAISS once
    faiss_index.save()

    db.close()

    print("Ingestion complete.")


if __name__ == "__main__":
    main()