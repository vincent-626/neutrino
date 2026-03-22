import numpy as np


def top_k_results(
    line_vecs: np.ndarray,
    query_vec: np.ndarray,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return indices and scores of top-k most similar log lines.

    line_vecs: shape (N, D), unit-normalized
    query_vec: shape (D,), unit-normalized
    Returns (indices, scores) both shape (k,), descending by score.
    """
    n = len(line_vecs)
    if n == 0:
        return np.array([], dtype=np.intp), np.array([], dtype=np.float32)

    k = min(k, n)
    scores = line_vecs @ query_vec  # shape (N,) — dot product = cosine sim

    # Efficient top-k via argpartition (O(N) vs O(N log N) sort)
    idx = np.argpartition(scores, -k)[-k:]
    idx = idx[np.argsort(scores[idx])[::-1]]

    return idx, scores[idx]
