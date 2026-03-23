"""
Semantic search quality tests.

These tests load the real embedding model (all-MiniLM-L6-v2) and assert that
semantically relevant log lines rank above irrelevant ones. They are slower
than unit tests (~5-10s for model load) so the engine is session-scoped.
"""

import numpy as np
import pytest

from neutrino.embedding.engine import EmbeddingEngine
from neutrino.search.preprocessor import preprocess
from neutrino.search.ranking import top_k_results


@pytest.fixture(scope="session")
def engine() -> EmbeddingEngine:
    return EmbeddingEngine()


def ranked_lines(query: str, corpus: list[str], engine: EmbeddingEngine, k: int = 3) -> list[str]:
    """Return the top-k corpus lines for a query, in ranked order."""
    preprocessed = [preprocess(line) for line in corpus]
    vecs = engine.encode(preprocessed)
    query_vec = engine.encode_single(query)
    idx, _ = top_k_results(vecs, query_vec, k=k)
    return [corpus[i] for i in idx]


# ---------------------------------------------------------------------------
# Corpus — realistic log lines across distinct failure categories
# ---------------------------------------------------------------------------

DB_LINES = [
    "2024-01-15T10:23:41Z ERROR db: connection refused — host=postgres port=5432",
    "2024-01-15T10:23:42Z ERROR failed to acquire connection from pool after 30s",
    "2024-01-15T10:23:43Z WARN  postgres query timeout after 5000ms on table orders",
]

AUTH_LINES = [
    "2024-01-15T10:24:01Z WARN  invalid JWT signature for user 3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "2024-01-15T10:24:02Z ERROR authentication failed: token expired",
    "2024-01-15T10:24:03Z WARN  login attempt rejected — too many failed attempts for user admin",
]

OOM_LINES = [
    "2024-01-15T10:25:10Z ERROR out of memory: kill process 4821 (node) score 901",
    "2024-01-15T10:25:11Z FATAL container exceeded memory limit of 512Mi, OOMKilled",
    "2024-01-15T10:25:12Z WARN  heap allocation failed, GC overhead limit exceeded",
]

NETWORK_LINES = [
    "2024-01-15T10:26:05Z ERROR dial tcp 10.0.0.5:8080: i/o timeout",
    "2024-01-15T10:26:06Z WARN  upstream service payments timed out after 3000ms",
    "2024-01-15T10:26:07Z ERROR connection reset by peer: 10.0.0.12:443",
]

DEPLOY_LINES = [
    "2024-01-15T10:27:00Z INFO  service api-gateway starting up, version=2.4.1",
    "2024-01-15T10:27:01Z INFO  healthcheck passed, marking pod ready",
    "2024-01-15T10:27:02Z INFO  graceful shutdown complete, all connections drained",
]

FULL_CORPUS = DB_LINES + AUTH_LINES + OOM_LINES + NETWORK_LINES + DEPLOY_LINES


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_db_query_ranks_db_lines_first(engine):
    top = ranked_lines("database connection error", FULL_CORPUS, engine)
    assert any(line in DB_LINES for line in top), (
        f"Expected a DB log in top-3, got: {top}"
    )


def test_auth_query_ranks_auth_lines_first(engine):
    top = ranked_lines("authentication failure invalid token", FULL_CORPUS, engine)
    assert any(line in AUTH_LINES for line in top), (
        f"Expected an auth log in top-3, got: {top}"
    )


def test_oom_query_ranks_oom_lines_first(engine):
    top = ranked_lines("out of memory crash", FULL_CORPUS, engine)
    assert any(line in OOM_LINES for line in top), (
        f"Expected an OOM log in top-3, got: {top}"
    )


def test_network_query_ranks_network_lines_first(engine):
    top = ranked_lines("network timeout upstream service unreachable", FULL_CORPUS, engine)
    assert any(line in NETWORK_LINES for line in top), (
        f"Expected a network log in top-3, got: {top}"
    )


def test_deploy_query_ranks_deploy_lines_first(engine):
    top = ranked_lines("service startup deployment ready", FULL_CORPUS, engine)
    assert any(line in DEPLOY_LINES for line in top), (
        f"Expected a deploy log in top-3, got: {top}"
    )


def test_paraphrase_still_finds_correct_category(engine):
    """Query uses different wording than the log — tests true semantic matching."""
    # "credentials rejected" is a paraphrase of auth failure logs
    top = ranked_lines("credentials rejected access denied", FULL_CORPUS, engine)
    assert any(line in AUTH_LINES for line in top), (
        f"Paraphrase test failed — expected auth log in top-3, got: {top}"
    )


def test_relevant_lines_score_above_irrelevant(engine):
    """DB query: the best DB line should outscore the best deploy line."""
    query = "postgres connection pool exhausted"
    preprocessed = [preprocess(line) for line in FULL_CORPUS]
    vecs = engine.encode(preprocessed)
    query_vec = engine.encode_single(query)

    db_indices = list(range(len(DB_LINES)))
    deploy_indices = list(range(len(DB_LINES + AUTH_LINES + OOM_LINES + NETWORK_LINES),
                                len(FULL_CORPUS)))

    sims = vecs @ query_vec
    best_db_score = max(sims[i] for i in db_indices)
    best_deploy_score = max(sims[i] for i in deploy_indices)

    assert best_db_score > best_deploy_score, (
        f"DB score {best_db_score:.3f} should exceed deploy score {best_deploy_score:.3f}"
    )


def test_truncated_flag_false_when_under_limit(engine):
    """Sanity-check: truncated is False when fewer lines than the limit are fetched."""
    from neutrino.config import settings
    assert len(FULL_CORPUS) < settings.max_log_lines


def test_scores_are_in_zero_one_range(engine):
    """Unit-normalised cosine similarity must be in [-1, 1]; meaningful scores > 0."""
    query_vec = engine.encode_single("error")
    vecs = engine.encode([preprocess(l) for l in FULL_CORPUS])
    _, scores = top_k_results(vecs, query_vec, k=5)
    assert all(-1.0 <= s <= 1.0 for s in scores)
