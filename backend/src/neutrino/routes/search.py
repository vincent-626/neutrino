import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated

from neutrino.config import settings
from neutrino.models import LabelsResponse, LogResult, SearchRequest, SearchResponse
from neutrino.loki.client import LokiClient
from neutrino.embedding.engine import EmbeddingEngine
from neutrino.embedding.cache import EmbeddingCache
from neutrino.search.preprocessor import preprocess
from neutrino.search.ranking import top_k_results

router = APIRouter()

# Module-level singletons — set by lifespan
_engine: EmbeddingEngine | None = None
_cache: EmbeddingCache | None = None
_loki: LokiClient | None = None


def init(engine: EmbeddingEngine, cache: EmbeddingCache, loki: LokiClient) -> None:
    global _engine, _cache, _loki
    _engine = engine
    _cache = cache
    _loki = loki


def _get_engine() -> EmbeddingEngine:
    if _engine is None:
        raise HTTPException(status_code=503, detail="Model not ready")
    return _engine


def _get_cache() -> EmbeddingCache:
    assert _cache is not None
    return _cache


def _get_loki() -> LokiClient:
    assert _loki is not None
    return _loki


@router.post("/search", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    engine: Annotated[EmbeddingEngine, Depends(_get_engine)],
    cache: Annotated[EmbeddingCache, Depends(_get_cache)],
    loki: Annotated[LokiClient, Depends(_get_loki)],
) -> SearchResponse:
    k = req.top_k or settings.top_k

    # 1. Fetch logs from Loki
    raw_lines = await loki.query_range(
        start_ns=req.start_ns,
        end_ns=req.end_ns,
        service=req.service,
        severity=req.severity,
        limit=settings.max_log_lines,
    )

    if not raw_lines:
        return SearchResponse(results=[], total_fetched=0)

    timestamps = [ts for ts, _, _ in raw_lines]
    label_dicts = [labels for _, labels, _ in raw_lines]
    lines = [line for _, _, line in raw_lines]

    # 2. Preprocess for embedding
    preprocessed = [preprocess(line) for line in lines]

    # 3. Check cache, embed misses
    cached_vecs, missing_idx = cache.get_or_missing(preprocessed)

    if missing_idx:
        missing_texts = [preprocessed[i] for i in missing_idx]
        new_vecs = engine.encode(missing_texts)
        cache.set_many(missing_texts, new_vecs)
        for j, i in enumerate(missing_idx):
            cached_vecs[i] = new_vecs[j]

    line_vecs = np.stack(cached_vecs)  # shape (N, D)

    # 4. Embed query
    query_vec = engine.encode_single(req.query)

    # 5. Rank
    idx, scores = top_k_results(line_vecs, query_vec, k=k)

    results = [
        LogResult(
            score=float(scores[rank]),
            timestamp_ns=timestamps[i],
            labels=label_dicts[i],
            line=lines[i],
        )
        for rank, i in enumerate(idx)
    ]

    return SearchResponse(
        results=results,
        total_fetched=len(raw_lines),
        truncated=len(raw_lines) >= settings.max_log_lines,
    )


@router.get("/labels", response_model=LabelsResponse)
async def labels(
    name: Annotated[str, Query(description="Label name to fetch values for")],
    loki: Annotated[LokiClient, Depends(_get_loki)],
) -> LabelsResponse:
    values = await loki.label_values(name)
    return LabelsResponse(values=values)
