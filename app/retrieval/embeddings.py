"""Embedding service for curriculum RAG pipeline."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Local TF-IDF based embedding service for curriculum retrieval.

    Uses TF-IDF vectors as a lightweight, zero-dependency embedding approach.
    No external API calls needed — fast, deterministic, and free.
    """

    def __init__(self):
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self._fitted = False
        self._corpus: list[str] = []
        self._matrix = None

    def fit(self, documents: list[str]) -> None:
        """Fit the vectorizer on a corpus of documents."""
        self._corpus = documents
        self._matrix = self._vectorizer.fit_transform(documents)
        self._fitted = True
        logger.info("embeddings_fitted", document_count=len(documents))

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string."""
        if not self._fitted:
            raise RuntimeError("EmbeddingService not fitted. Call fit() first.")
        return self._vectorizer.transform([query])

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """Search for most similar documents to a query.

        Returns list of (document_index, similarity_score) tuples.
        """
        if not self._fitted:
            return []

        query_vec = self.embed_query(query)
        similarities = cosine_similarity(query_vec, self._matrix).flatten()

        # Get top-k indices sorted by similarity
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [
            (int(idx), float(similarities[idx]))
            for idx in top_indices
            if similarities[idx] > 0.0
        ]
        return results
