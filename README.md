# Neutrino

**Semantic log search for Grafana Loki.** Find logs by meaning, not just keywords.

Neutrino adds a search mode to Grafana Explore. Type a natural language query like _"database connection refused"_ and get back the most semantically similar log lines — ranked by cosine similarity using a local embedding model. No external APIs. No changes to your Loki setup.

---

## How it works

Neutrino appears in the **Add** dropdown in Grafana Explore. Select a service and time range, type a query, and results appear ranked by similarity score with a **View in LogQL →** button to pivot back to native Explore for each result.

```
Browser → Grafana plugin API → Go proxy → Python/FastAPI → Loki HTTP API
                                               ↓
                                    SentenceTransformer
                                    (all-MiniLM-L6-v2, local)
```

The query pipeline:

1. Builds a LogQL query from your service/severity filters and fetches log lines from Loki
2. Strips timestamps, UUIDs, IPs, and path IDs from each line before embedding
3. Encodes every line and your query into 384-dim vectors using `all-MiniLM-L6-v2`
4. Returns the top-K results ranked by cosine similarity
5. Embeddings are cached by content hash — repeat queries over the same window are fast

---

## Getting started

**Prerequisites:** Docker, Go 1.22+, [Mage](https://magefile.org/), Node.js 20+, pnpm

```bash
# Install dependencies
cd plugin && go mod tidy && pnpm install && cd ..

# Build Go binary + frontend bundle
make dist

# Start the full stack (Grafana, Loki, Neutrino backend, log generator)
make dev
```

Open [http://localhost:3000](http://localhost:3000) (admin / admin), go to **Explore**, select the **Loki** datasource, and open **Neutrino** from the **Add** dropdown.

---

## Development

```bash
# Terminal 1 — Loki + log generator in Docker
make dev-native

# Terminal 2 — Python backend with hot reload
make run-backend

# Terminal 3 — Frontend in watch mode
make dev-plugin
```

### Running tests

```bash
make test-backend
```

Includes unit tests for the LogQL builder, preprocessor, and ranking, plus semantic quality tests that load the real embedding model and assert correct retrieval against a fixture log corpus.

### Build targets

| Target | Description |
|---|---|
| `make dist` | Full build: Go binary for host arch + frontend bundle |
| `make dev` | Build dist, then start full Docker Compose stack |
| `make dev-native` | Start Loki + flog + promtail only |
| `make dev-plugin` | Frontend watch mode |
| `make run-backend` | Python backend with `--reload` |
| `make build-backend-plugin` | Go binary for current host arch |
| `make build-backend-plugin-all` | Go binaries for linux/amd64 and linux/arm64 |
| `make test-backend` | Run Python backend tests |

---

## Configuration

**Python backend** (environment variables):

| Variable | Default | Description |
|---|---|---|
| `LOKI_URL` | `http://loki:3100` | Loki base URL |
| `MAX_LOG_LINES` | `5000` | Max lines fetched per query — a warning is shown in the UI if the limit is hit |
| `TOP_K` | `25` | Number of results returned |
| `CACHE_TTL_SECONDS` | `21600` | Embedding cache TTL (6 hours) |

**Go backend plugin** (environment variables, set on the Grafana container):

| Variable | Default | Description |
|---|---|---|
| `NEUTRINO_BACKEND_URL` | `http://localhost:8400` | URL of the Python backend |

---

## Repository layout

```
neutrino/
├── Makefile
├── backend/                    # Python FastAPI service
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/neutrino/
│       ├── main.py             # FastAPI app + lifespan
│       ├── config.py           # Env-var settings
│       ├── models.py           # Pydantic request/response types
│       ├── routes/             # health, search, labels endpoints
│       ├── loki/               # Loki HTTP client + LogQL builder
│       ├── embedding/          # SentenceTransformer wrapper + LRU cache
│       └── search/             # Log preprocessor + cosine ranking
├── plugin/                     # Grafana app plugin
│   ├── plugin.json
│   ├── pkg/                    # Go proxy backend
│   └── src/                    # TypeScript/React frontend
│       ├── module.tsx          # Extension point registration
│       ├── components/         # NeutrinoModal, QueryInput, ResultsList, …
│       └── utils/logql.ts      # "View in LogQL" URL builder
└── deploy/                     # Docker Compose + config
    ├── docker-compose.yml
    ├── grafana/                 # grafana.ini + provisioning
    ├── loki/
    └── promtail/
```

---

## Limitations

- **Negation isn't captured** — "connection succeeded" and "connection failed" are close in embedding space. Searches for failures may surface successes.
- **Structured/coded logs** — `ERR_CODE=5023` is mostly opaque. The model doesn't know what internal codes mean.
- **Requires a coarse filter** — A service and time range must be set before searching. Searching all logs across all services at once isn't practical.
- **No vocabulary learning** — The model doesn't adapt to your team's internal terminology or error codes.

---

## License

MIT
