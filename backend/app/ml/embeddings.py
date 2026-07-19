"""Text embeddings for semantic dedup and engine comparison.

Primary backend is sentence-transformers (real semantic similarity). When
that model can't be loaded (offline environment, no download, CI), we fall
back to a deterministic pure-numpy hashing/TF vectorizer so dedup and the
compare endpoint still work — just lexically rather than semantically.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class _HashingEmbedder:
    """Lexical fallback: hash unigrams+bigrams into a fixed-dim TF vector."""

    backend = "hashing-tfidf"
    dim = 512

    def _tokens(self, text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
        return words + bigrams

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in self._tokens(text):
                vecs[i, hash(tok) % self.dim] += 1.0
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms


class _SentenceTransformerEmbedder:
    """Semantic backend backed by sentence-transformers."""

    backend = "sentence-transformers"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.backend = f"sentence-transformers:{model_name}"

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self._model.encode(texts, normalize_embeddings=True), dtype=np.float32
        )


@lru_cache(maxsize=1)
def get_embedder():
    """Return the best available embedder, cached for the process lifetime."""
    model_name = get_settings().embedding_model
    try:
        embedder = _SentenceTransformerEmbedder(model_name)
        logger.info("Embeddings backend: %s", embedder.backend)
        return embedder
    except Exception as exc:  # model unavailable / offline
        logger.warning(
            "Falling back to lexical embedder (%s unavailable): %s", model_name, exc
        )
        return _HashingEmbedder()


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity between rows of a and rows of b (rows are L2-normalized)."""
    if a.size == 0 or b.size == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype=np.float32)
    return a @ b.T
