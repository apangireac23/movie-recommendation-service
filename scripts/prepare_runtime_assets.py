from pathlib import Path

import faiss


INDEX_PATH = Path("index.faiss")
IDS_PATH = Path("index_ids.json")


def main():
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing runtime FAISS index: {INDEX_PATH}")

    if not IDS_PATH.exists():
        raise FileNotFoundError(f"Missing runtime id map: {IDS_PATH}")

    index = faiss.read_index(str(INDEX_PATH))
    print(f"Validated {INDEX_PATH} with {index.ntotal} vectors")
    print(f"Validated {IDS_PATH}")


if __name__ == "__main__":
    main()
