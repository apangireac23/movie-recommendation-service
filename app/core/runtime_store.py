"""Module-level singletons shared across the service.

Keeping these here avoids circular imports between `app.main` and
`app.services.recommender`: both import `faiss_index` from this module.
"""

from app.ml.faiss_index import FaissIndex

faiss_index = FaissIndex()
