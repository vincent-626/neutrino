FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install deps first (layer cache)
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

# Bake the embedding model into the image so startup is instant
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy source
COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8400

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8400/readyz')"

CMD ["uv", "run", "uvicorn", "neutrino.main:app", "--host", "0.0.0.0", "--port", "8400"]
