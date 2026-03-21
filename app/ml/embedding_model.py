from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_load_error = None


def _get_model():
    global _model, _load_error

    if _model is not None:
        return _model

    if _load_error is not None:
        return None

    try:
        # Avoid network-dependent startup; use a cached local model if present.
        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception as exc:
        _load_error = exc
        return None

    return _model


def generate_embedding(text: str):
    model = _get_model()

    if model is None:
        return None

    return model.encode(text, normalize_embeddings=True)
