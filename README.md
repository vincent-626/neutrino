# Neutrino

**Semantic search for Grafana Loki.** Find logs by meaning, not just keywords.

Neutrino adds a toolbar button to Grafana Explore. Click it, type a natural language query like _"database connection refused"_, and get back the most semantically similar log lines — ranked by cosine similarity using a local embedding model. No external APIs. No changes to your Loki setup.

---

## How it works

1. You pick a service and time range (inherited from Explore), then type a query
2. Neutrino fetches matching logs from Loki via LogQL
3. A local `all-MiniLM-L6-v2` model embeds every log line and your query
4. Results are ranked by cosine similarity and returned in under a second (warm cache)
5. "View in LogQL →" on any result pivots back to the native Explore log view

```
Browser → Grafana plugin API → Go proxy → Python/FastAPI → Loki HTTP API
                                                ↓
                                     SentenceTransformer
                                     (all-MiniLM-L6-v2, local)
```

---

## Prerequisites

- Docker + Docker Compose
- Go 1.22+ and [Mage](https://magefile.org/) (`go install github.com/magefile/mage@latest`)
- Node.js 20+ and npm

---

## Quickstart

```bash
# 1. Install dependencies
cd plugin && go mod tidy && pnpm install && cd ..

# 2. Build the full plugin dist (Linux Go binary + frontend bundle)
make dist

# 3. Start everything
make dev
```

Open [http://localhost:3000](http://localhost:3000) (admin / admin), go to **Explore**, select the **Loki** datasource, and click the **Neutrino 🔍** button in the toolbar.

---

## Development

### Run backend natively (faster iteration)

```bash
# Terminal 1 — Loki + log generator in Docker
make dev-native

# Terminal 2 — Python backend with hot reload
make run-backend

# Terminal 3 — Frontend in watch mode
make dev-plugin
```

Then open Grafana at localhost:3000.

### Run tests

```bash
make test-backend
```

### Build targets

| Target | Description |
|--------|-------------|
| `make dev` | Full Docker Compose stack (all 5 containers) |
| `make dev-native` | Loki + flog + promtail only (run backend/plugin natively) |
| `make dev-plugin` | Frontend watch mode |
| `make run-backend` | Python backend with `--reload` |
| `make build-backend-plugin` | Go binary for current platform |
| `make build-backend-plugin-linux` | Go binary for linux/amd64 |
| `make build-plugin` | TypeScript frontend bundle |
| `make dist` | Full dist build (linux Go + frontend) |
| `make test-backend` | Run Python backend tests |

---

## Repository layout

```
neutrino/
├── Makefile
├── backend/                       # Python FastAPI service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/neutrino/
│       ├── main.py                # FastAPI app + lifespan
│       ├── config.py              # Env-var settings
│       ├── models.py              # Pydantic request/response types
│       ├── routes/                # health, search, labels endpoints
│       ├── loki/                  # Loki HTTP client + LogQL builder
│       ├── embedding/             # SentenceTransformer wrapper + LRU cache
│       └── search/                # Log preprocessor + cosine ranking
├── plugin/                        # Grafana app plugin (Go + TypeScript)
│   ├── plugin.json
│   ├── pkg/                       # Go backend — proxies to Python service
│   └── src/                       # TypeScript frontend
│       ├── module.ts              # ExploreToolbarAction registration
│       ├── components/            # NeutrinoDrawer, QueryInput, ResultsList, …
│       └── utils/logql.ts         # "View in LogQL" URL builder
└── deploy/                        # Docker Compose + config
    ├── docker-compose.yml
    ├── grafana/                   # grafana.ini + provisioning
    ├── loki/                      # Loki monolithic config
    └── promtail/                  # Promtail scrape config
```

---

## Configuration

The Python backend is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOKI_URL` | `http://loki:3100` | Loki base URL |
| `CACHE_TTL_SECONDS` | `21600` | Embedding cache TTL (6 hours) |
| `MAX_LOG_LINES` | `10000` | Hard cap on lines fetched per query |
| `TOP_K` | `25` | Number of results returned |

The Go backend plugin reads:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEUTRINO_BACKEND_URL` | `http://localhost:8400` | URL of the Python backend |

---

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a full description of components, the query pipeline, deployment options, caching strategy, and known limitations.

---

## Limitations

- Works best on natural-language-style log messages. Structured/coded logs (`ERR_CODE=5023`) are opaque to the model.
- "connection succeeded" and "connection failed" are close in embedding space — negation isn't well-captured.
- Requires a coarse filter (service + time range) before searching. Searching all logs across all services at once isn't practical.
- The embedding model doesn't learn your team's internal vocabulary or error codes.
