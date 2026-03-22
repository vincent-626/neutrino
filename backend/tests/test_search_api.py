import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
from fastapi.testclient import TestClient

from neutrino.main import app
from neutrino.routes import health, search
from neutrino.embedding.engine import EmbeddingEngine
from neutrino.embedding.cache import EmbeddingCache
from neutrino.loki.client import LokiClient


@pytest.fixture
def client():
    # Stub out the singletons so we don't need a real model or Loki
    engine = MagicMock(spec=EmbeddingEngine)
    cache = EmbeddingCache(maxsize=10, ttl_seconds=60)
    loki = MagicMock(spec=LokiClient)

    search.init(engine=engine, cache=cache, loki=loki)
    health.set_ready(True)

    with TestClient(app) as c:
        yield c, engine, loki


def test_healthz(client):
    c, _, _ = client
    resp = c.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_when_ready(client):
    c, _, _ = client
    health.set_ready(True)
    resp = c.get("/readyz")
    assert resp.status_code == 200


def test_readyz_when_not_ready():
    health.set_ready(False)
    with TestClient(app) as c:
        resp = c.get("/readyz")
    assert resp.status_code == 503
    health.set_ready(True)


def test_search_returns_results(client):
    c, engine, loki = client

    loki.query_range = AsyncMock(return_value=[
        (1_700_000_000_000_000_000, {"service": "payments"}, "Failed DB connection"),
        (1_700_000_000_100_000_000, {"service": "payments"}, "DB timeout on write"),
    ])

    # Return unit vectors for all encode calls
    vec_a = np.array([1.0] + [0.0] * 383, dtype=np.float32)
    vec_b = np.array([0.0, 1.0] + [0.0] * 382, dtype=np.float32)
    query_vec = np.array([1.0] + [0.0] * 383, dtype=np.float32)

    engine.encode = MagicMock(return_value=np.stack([vec_a, vec_b]))
    engine.encode_single = MagicMock(return_value=query_vec)

    resp = c.post("/search", json={
        "query": "database connection issues",
        "service": "payments",
        "start_ns": 1_700_000_000_000_000_000,
        "end_ns": 1_700_003_600_000_000_000,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fetched"] == 2
    assert len(data["results"]) == 2
    # vec_a is identical to query_vec → score ≈ 1.0
    assert data["results"][0]["score"] == pytest.approx(1.0, abs=1e-4)


def test_search_empty_loki(client):
    c, engine, loki = client
    loki.query_range = AsyncMock(return_value=[])
    resp = c.post("/search", json={
        "query": "anything",
        "start_ns": 0,
        "end_ns": 1,
    })
    assert resp.status_code == 200
    assert resp.json()["total_fetched"] == 0
    assert resp.json()["results"] == []
