from contextlib import asynccontextmanager
from fastapi import FastAPI

from neutrino.config import settings
from neutrino.embedding.engine import EmbeddingEngine
from neutrino.embedding.cache import EmbeddingCache
from neutrino.loki.client import LokiClient
from neutrino.routes import health, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model before accepting traffic
    engine = EmbeddingEngine(model_name=settings.model_name)
    cache = EmbeddingCache(ttl_seconds=settings.cache_ttl_seconds)
    loki = LokiClient(base_url=settings.loki_url)

    search.init(engine=engine, cache=cache, loki=loki)
    health.set_ready(True)

    yield

    health.set_ready(False)


app = FastAPI(title="Neutrino", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(search.router)
