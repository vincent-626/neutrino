import numpy as np
from sentence_transformers import SentenceTransformer
from neutrino.config import settings


class EmbeddingEngine:
    def __init__(self, model_name: str = settings.model_name):
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Encode a list of texts into unit-normalized embeddings.

        Returns shape (N, D) float32 array.
        With normalize_embeddings=True, cosine similarity = dot product.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        return self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text. Returns shape (D,) float32 array."""
        return self.encode([text])[0]
