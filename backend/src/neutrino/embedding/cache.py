import hashlib
import time
from collections import OrderedDict
from typing import Optional
import numpy as np

from neutrino.config import settings


class EmbeddingCache:
    """
    In-process LRU cache with TTL for log line embeddings.

    Key: SHA256(text) → value: (embedding: np.ndarray, expires_at: float)
    """

    def __init__(
        self,
        maxsize: int = 50_000,
        ttl_seconds: int = settings.cache_ttl_seconds,
    ):
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[np.ndarray, float]] = OrderedDict()

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        key = self._key(text)
        if key not in self._cache:
            return None
        vec, expires_at = self._cache[key]
        if time.monotonic() > expires_at:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return vec

    def set(self, text: str, embedding: np.ndarray) -> None:
        key = self._key(text)
        expires_at = time.monotonic() + self._ttl
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (embedding, expires_at)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def get_or_missing(
        self, texts: list[str]
    ) -> tuple[list[Optional[np.ndarray]], list[int]]:
        """
        For each text, return cached embedding or None.

        Returns (embeddings_or_none, missing_indices).
        """
        results: list[Optional[np.ndarray]] = []
        missing: list[int] = []
        for i, text in enumerate(texts):
            vec = self.get(text)
            results.append(vec)
            if vec is None:
                missing.append(i)
        return results, missing

    def set_many(self, texts: list[str], embeddings: np.ndarray) -> None:
        for text, vec in zip(texts, embeddings):
            self.set(text, vec)
