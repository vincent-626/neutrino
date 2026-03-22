import numpy as np
import pytest
from neutrino.search.ranking import top_k_results


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def test_top_k_returns_k_results():
    rng = np.random.default_rng(42)
    vecs = np.array([_unit(rng.random(384)) for _ in range(100)], dtype=np.float32)
    query = _unit(rng.random(384)).astype(np.float32)
    idx, scores = top_k_results(vecs, query, k=10)
    assert len(idx) == 10
    assert len(scores) == 10


def test_top_k_scores_descending():
    rng = np.random.default_rng(0)
    vecs = np.array([_unit(rng.random(384)) for _ in range(50)], dtype=np.float32)
    query = _unit(rng.random(384)).astype(np.float32)
    _, scores = top_k_results(vecs, query, k=5)
    assert list(scores) == sorted(scores, reverse=True)


def test_top_k_prefers_similar_vector():
    # query is identical to vecs[3]
    rng = np.random.default_rng(7)
    vecs = np.array([_unit(rng.random(384)) for _ in range(20)], dtype=np.float32)
    query = vecs[3].copy()
    idx, scores = top_k_results(vecs, query, k=1)
    assert idx[0] == 3
    assert scores[0] == pytest.approx(1.0, abs=1e-5)


def test_top_k_fewer_than_k_lines():
    vecs = np.array([_unit(np.array([1.0, 0.0]))] * 3, dtype=np.float32)
    query = np.array([1.0, 0.0], dtype=np.float32)
    idx, scores = top_k_results(vecs, query, k=10)
    assert len(idx) == 3


def test_top_k_empty():
    vecs = np.empty((0, 384), dtype=np.float32)
    query = np.zeros(384, dtype=np.float32)
    idx, scores = top_k_results(vecs, query, k=5)
    assert len(idx) == 0
    assert len(scores) == 0
