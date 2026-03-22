# Neutrino

**Semantic Search Plugin for Grafana Loki**

> Find logs by meaning, not just keywords.

---

## Overview

Neutrino is a Grafana plugin that adds semantic search capability to Loki. It enables engineers to search logs using natural language queries and surface semantically related log lines — even when they don't share keywords.

Neutrino does not replace LogQL. It runs alongside it as an optional search mode for exploratory debugging, designed to help engineers find what they're looking for when they don't know the exact terms.

### Design Principles

- **No external LLM dependency.** All inference runs locally using lightweight sentence embedding models. No data leaves your infrastructure.
- **Additive, not replacing.** Neutrino lives inside the Grafana Explore view as an entry in the **Add** dropdown menu. It doesn't replace LogQL — it's an extra mode engineers reach for when keyword search isn't enough.
- **Loki-first.** Loki's indexing and storage do the heavy lifting. Neutrino only operates on a pre-filtered subset of logs.
- **Predictable cost.** No per-query API fees. The embedding service is a fixed-cost container.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Grafana Explore View                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  [ LogQL query editor ]            [ Add ▾ ]              │  │
│  │                                      └─ Neutrino 🔍       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                            │  │
│  │  Neutrino Modal (opens after selecting from Add menu)      │  │
│  │                                                            │  │
│  │  ┌──────────────┐ ┌──────────┐ ┌──────────────────┐      │  │
│  │  │ Service      │ │ Severity │ │ Time Range       │      │  │
│  │  │ Label        │ │ Filter   │ │ (shared w/       │      │  │
│  │  │ Selector     │ │          │ │  Explore)        │      │  │
│  │  └──────────────┘ └──────────┘ └──────────────────┘      │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  🔍  "database connection issues"                    │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  Ranked Results                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  0.94  03:22:41  [pay-svc] Failed to acquire        │  │  │
│  │  │                  connection to pg pool               │  │  │
│  │  │  0.91  03:22:38  [pay-svc] Database health check    │  │  │
│  │  │                  timeout after 30s                   │  │  │
│  │  │  0.87  03:21:55  [pay-svc] ETIMEDOUT on             │  │  │
│  │  │                  upstream db connection              │  │  │
│  │  │  0.82  03:21:02  [pay-svc] Retry exhausted for      │  │  │
│  │  │                  database write operation            │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │        [ View in LogQL → ]   ← opens result context       │  │
│  │                                in native Explore/LogQL     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
          API call (same-process)
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Neutrino Backend Plugin (Go)                     │
│         Runs inside Grafana process                      │
│         Proxies requests to Neutrino backend service     │
└──────────────────┬──────────────────────────────────────┘
                   │
          Forwarded HTTP request
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Neutrino Backend Service                    │
│              (Python / FastAPI)                          │
│                                                         │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Loki Client    │  │  Embedding   │  │  Vector       │  │
│  │                 │  │  Engine      │  │  Search       │  │
│  │  Builds LogQL   │  │              │  │               │  │
│  │  from filters,  │  │  MiniLM-L6   │  │  In-memory    │  │
│  │  calls HTTP API │  │  sentence-   │  │  cosine sim   │  │
│  │                 │  │  transformers│  │  ranking      │  │
│  └────────┬────────┘  └──────────────┘  └───────────────┘  │
│           │                                                 │
│           │           ┌──────────────┐                      │
│           │           │  Embedding   │                      │
│           │           │  Cache       │                      │
│           │           │              │                      │
│           │           │  In-process  │                      │
│           │           │  LRU         │                      │
│           │           └──────────────┘                      │
└──────────┼──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│     Loki Cluster     │
│                      │
│  Label index +       │
│  chunk storage       │
│  (unchanged)         │
└──────────────────────┘
```

---

## Components

### 1. Neutrino Explore Extension (Grafana Frontend)

A Grafana **app plugin** that registers an **`ExploreToolbarAction`** extension. A "Neutrino 🔍" button appears in the Explore toolbar. Clicking it opens a drawer below the query editor with the full Neutrino UI — service selector, severity filter, query input, and ranked results.

> **Architecture note:** Grafana 10.x does not support peer tabs or standalone toolbar buttons as extension points. Plugin link extensions registered at `grafana/explore/toolbar/action` appear as items inside Grafana's built-in **Add** dropdown in the Explore toolbar. Clicking the entry opens a modal via `openModal` from the extension event helpers.

**Why an app plugin with an Explore toolbar action (not a datasource fork):**

- Grafana's app plugin type supports registering `ExploreToolbarAction` extensions, giving Neutrino a native feel without forking or extending the Loki datasource plugin.
- The Loki datasource is actively developed upstream. Forking it means tracking merge conflicts on every Grafana release. An app plugin has its own lifecycle and is immune to Loki datasource updates.
- Neutrino's results (ranked by similarity score) don't fit neatly into the standard data frame contract that Grafana's Explore view expects from datasource plugins. A custom drawer component gives full control over rendering.

**Shared context with Explore:**

- The time range picker is shared — Neutrino inherits the time range the user has already set in Explore, so there's no duplicate time picker.
- The Loki datasource is shared — Neutrino knows which Loki instance to query based on the datasource already selected in Explore. No second datasource picker needed.
- Service label selector and severity filter are Neutrino-specific UI, rendered within the extension tab.

**Key interactions:**

- "View in LogQL" button on any result — constructs a LogQL query scoped to the timestamp and stream labels of that result, then switches the user back to the LogQL tab with that query pre-filled. This lets engineers pivot from "I found something interesting via semantic search" to "show me the full log context around this line" in one click.
- Results render with similarity scores, timestamps, stream labels, and the full log line — matching the visual language of Explore's existing log view as closely as possible to reduce cognitive overhead.

**Tech:** TypeScript, React, Grafana Plugin SDK (`@grafana/data`, `@grafana/ui`, `@grafana/runtime`). Registered via `addComponent` targeting the `grafana/explore/toolbar/action` extension point.

### 2. Neutrino Backend Plugin (Go)

A lightweight Go backend component that ships as part of the Grafana app plugin. Grafana loads it into the Grafana server process at plugin startup.

**Why this is needed:** The Neutrino frontend runs in the browser, which cannot reach `http://neutrino.monitoring.svc.cluster.local:8400` directly — that address is only resolvable inside the cluster. The backend plugin acts as a transparent proxy: the browser calls Grafana's plugin API, and the backend plugin forwards the request to the Neutrino backend service over in-cluster DNS.

**Responsibilities:**
- Receive search requests from the frontend plugin via Grafana's plugin RPC mechanism
- Forward requests to the Neutrino backend service and stream the response back
- Read `NEUTRINO_BACKEND_URL` from the Grafana environment to know where to forward

**Tech:** Go (required by Grafana's backend plugin SDK — `grafana-plugin-sdk-go`).

### 3. Neutrino Backend Service

A lightweight API service that orchestrates the search pipeline.

**Responsibilities:**

- **Loki Client** — Constructs a LogQL query from the structured UI inputs (labels, time range, severity) and executes it against the Loki HTTP API (`/loki/api/v1/query_range`). The query construction is deterministic string formatting — example: `service=payments`, `last 1h`, `severity>=warn` → `{service="payments"} | severity >= "warn"`.
- **Embedding Engine** — Encodes log lines and the user's natural language query into vector representations using a local sentence transformer model.
- **Vector Search** — Performs in-memory cosine similarity between the query vector and all log line vectors. Returns top-N results ranked by similarity score.
- **Embedding Cache** — Caches embeddings keyed by a hash of the log line content. Log lines don't change, so cached embeddings are valid indefinitely within a reasonable TTL (e.g., 6 hours). This means repeat queries against the same time window skip embedding entirely.

**Tech:** Python, FastAPI, sentence-transformers, NumPy.

### 3. Embedding Model

**Default model:** `all-MiniLM-L6-v2`

- 80MB model size.
- 384-dimensional embeddings.
- ~1000 embeddings/second on CPU, ~5000+ on GPU.
- No external API calls. Runs entirely within the service container.

This model is a reasonable starting point. It handles natural-language-like log messages well. See [Limitations](#limitations) for where it struggles.

---

## Query Flow

```
1. User enters query (in Neutrino drawer within Explore)
   ├── Time range inherited from Explore: last 1h
   ├── Loki datasource inherited from Explore
   ├── Selects: service=payments, severity >= warn
   └── Types: "database connection issues"

2. Neutrino backend receives structured request

3. LogQL Builder constructs query
   → {service="payments"} | severity >= "warn"
   → time range: now-1h to now

4. Loki Client executes query
   → Returns ~2,400 log lines

5. Embedding Engine
   ├── Check cache: 1,800 lines already cached from earlier query
   ├── Embed remaining 600 new lines (~0.6s on CPU)
   └── Embed query string "database connection issues"

6. Vector Search
   ├── Cosine similarity: query vector vs all 2,400 line vectors
   ├── Rank by score
   └── Return top 25 results

7. Results displayed in Neutrino drawer within Explore
   ├── Each result shows: similarity score, timestamp,
   │   stream labels, full log line
   └── "View in LogQL →" switches to LogQL tab with
       a pre-filled query scoped to that result's context
```

---

## Deployment

Neutrino is designed to deploy into an existing Kubernetes cluster where Loki is already running. The backend ships as a Helm chart that drops into the same namespace as your Loki stack.

### Helm Installation

```bash
helm repo add neutrino https://charts.neutrino.dev
helm repo update

helm install neutrino neutrino/neutrino \
  --namespace monitoring \
  --set loki.url=http://loki-gateway.monitoring.svc.cluster.local:3100 \
  --set config.modelName=all-MiniLM-L6-v2 \
  --set config.maxLogLines=50000 \
  --set config.topK=25
```

This creates a Deployment and Service in your existing monitoring namespace. Neutrino discovers Loki via the in-cluster service DNS — no ingress or external networking required.

### Helm Values

```yaml
# values.yaml
loki:
  url: http://loki-gateway.monitoring.svc.cluster.local:3100

config:
  modelName: all-MiniLM-L6-v2
  cacheTTLSeconds: 21600        # 6 hours
  maxLogLines: 50000            # hard cap per query
  topK: 25                      # default results returned

replicas: 2                     # scale horizontally for concurrent users

resources:
  requests:
    cpu: "1"
    memory: 1Gi
  limits:
    cpu: "2"
    memory: 2Gi

# Optional: enable GPU for higher throughput
gpu:
  enabled: false
  # nvidia.com/gpu: 1           # uncomment for GPU mode

serviceMonitor:
  enabled: true                 # if you're running Prometheus Operator
```

### What the Helm Chart Creates

```
namespace: monitoring (existing)
│
├── Deployment: neutrino-backend (N replicas)
│   ├── Container: neutrino (FastAPI + embedding model)
│   └── Probes: /healthz (liveness), /readyz (readiness, model loaded)
│
├── Service: neutrino (ClusterIP, port 8400)
│   └── Neutrino backend plugin connects here via in-cluster DNS
│
├── ConfigMap: neutrino-config
│   └── Model name, cache TTL, max log lines, top-K
│
├── ServiceMonitor (optional, if serviceMonitor.enabled)
│   └── Scrapes /metrics for embedding latency, cache hit rate,
│       query volume, Loki fetch duration
│
└── HPA: neutrino-backend (optional)
    └── Scale on CPU utilization for bursty query load
```

### Service Discovery

Neutrino talks to Loki via Kubernetes service DNS. If your Loki is deployed with the standard Helm chart (Grafana's `loki` or `loki-distributed`), the gateway service is typically at `http://loki-gateway.<namespace>.svc.cluster.local:3100`. For Loki in monolithic mode, it's usually `http://loki.<namespace>.svc.cluster.local:3100`.

The Grafana plugin connects to the Neutrino backend via `http://neutrino.monitoring.svc.cluster.local:8400` — configured in the plugin settings within Grafana.

No external ingress is needed for any of this. All traffic stays in-cluster.

### Resource Requirements

| Component | CPU | Memory | GPU | Notes |
|-----------|-----|--------|-----|-------|
| Backend (CPU mode) | 1–2 cores | 1–2 GB | None | Suitable for most teams |
| Backend (GPU mode) | 1 core | 1–2 GB | 1x small GPU | 5x throughput, optional |
| Grafana plugin | — | — | — | Runs in existing Grafana instance |

### Grafana Configuration

Install the Neutrino app plugin into your Grafana instance. If Grafana is deployed via Helm, add the plugin to your Grafana values:

```yaml
# grafana values.yaml
plugins:
  - neutrino-semantic-search

env:
  NEUTRINO_BACKEND_URL: http://neutrino.monitoring.svc.cluster.local:8400
```

Once enabled, Neutrino appears as an entry in the **Add** dropdown in the Explore view (requires at least one query to be present in the pane). No changes to your existing Loki datasource configuration are required — Neutrino reads the Loki connection details from the datasource already configured in Grafana.

Minimum supported Grafana version: 10.0+ (required for Explore extension point APIs).

---

## Embedding Cache Strategy

Caching is critical to making repeated queries fast and keeping CPU usage reasonable.

**Cache key:** `SHA256(log_line_text)` → 384-dim float vector.

**Why this works:** Log line content is immutable. The same line will always produce the same embedding. Unlike a search engine index that needs to track document updates, log lines never change after they're written.

**Cache layer:**

| Layer | Scope | Latency | Use case |
|-------|-------|---------|----------|
| In-process LRU | Single replica | <1ms | Hot queries, same user repeating search |

**Cache miss cost:** ~1ms per line on CPU (batched). A fully uncached query over 10,000 lines takes ~10 seconds on CPU. With a warm cache, the same query returns in under 1 second.

**Multi-replica note:** Each replica maintains its own LRU. On first query after a pod restart the cache is cold; it warms quickly as queries repeat over the same time windows.

**Eviction:** TTL-based (default 6 hours). No need for complex invalidation since log data is append-only.

---

## Log Preprocessing Pipeline

Raw log lines are noisy. Before embedding, Neutrino applies a lightweight preprocessing step to improve embedding quality.

```
Raw log line
│
├── Strip timestamps (2024-01-15T03:22:41Z → removed)
├── Strip UUIDs and request IDs (a]8f3e2b1-... → <ID>)
├── Strip IP addresses (10.0.4.22 → <IP>)
├── Normalize paths (/api/v2/users/1234/orders → /api/v2/users/<ID>/orders)
└── Collapse whitespace and control characters

Preprocessed line → sent to embedding model
```

This normalization ensures that log lines differing only in variable parts (IDs, timestamps, IPs) produce similar embeddings. Without it, "Failed connecting to 10.0.4.22:5432" and "Failed connecting to 10.0.4.23:5432" would be slightly different in embedding space for no useful reason.

**The original raw log line is preserved and displayed in results.** Preprocessing only affects the text sent to the embedding model.

---

## Limitations

These are inherent to the approach and should be communicated to users.

### Semantic ceiling

Sentence embedding models map text to vectors based on surface-level semantic similarity. They don't "understand" logs the way a human does.

- **Structured/coded logs** — `ERR_CODE=5023 svc=pay gw=stripe` is mostly opaque to the model. It doesn't know what error code 5023 means.
- **Negation** — "connection succeeded" and "connection failed" are very close in embedding space. Searches for failures may surface successes too.
- **Stack traces** — Multi-line stack traces don't embed well as a single chunk. Neutrino treats each line independently, which loses cross-line context.

### Scope constraint

The user must provide an initial filter (service, time range) to narrow the log volume to something embeddable in reasonable time. Neutrino cannot search "all logs across all services" without a coarse filter first.

**Practical limits by deployment size:**

| Log lines in window | CPU embed time (uncached) | Feasibility |
|---------------------|---------------------------|-------------|
| 1,000 | ~1s | Instant |
| 10,000 | ~10s | Comfortable |
| 50,000 | ~50s | Upper bound, needs progress indicator |
| 100,000+ | Minutes | Not recommended; tighten filters |

### No learning

The model doesn't adapt to your organization's log vocabulary. Internal error codes, custom abbreviations, and domain-specific jargon remain opaque on day one and day three hundred.

**Mitigation (future):** An optional alias/synonym table where teams can map internal codes to natural language descriptions (e.g., `5023 → "Stripe refund failure"`). These descriptions would be appended to the log line before embedding.

### Ranking opacity

Cosine similarity scores are not intuitively interpretable. A score of 0.85 might be a great match or a mediocre one depending on the query and corpus. There's no universal threshold for "relevant."

---

## Future Considerations

These are explicitly out of scope for v1 but worth noting for later iterations.

- **Alias table** — Let teams define mappings from internal codes/abbreviations to natural language. Injected into the preprocessing step before embedding.
- **Cluster view** — Group semantically similar results into clusters, showing one representative line per cluster. Useful when the same error appears thousands of times with slight variations.
- **Fine-tuned model** — Train a custom embedding model on your organization's logs using contrastive learning. Requires labeled pairs of "these logs mean the same thing." Significant effort but large quality improvement.
- **Ingest-time embedding for high-value logs** — Selectively embed error/fatal level logs at ingest time into a persistent vector store. Enables broader searches without the query-time window constraint.
- **Streaming results** — Return results incrementally as batches of log lines are embedded, rather than waiting for the full window.

---

## Summary

Neutrino adds semantic search to Loki as a Grafana plugin. It works by using Loki's existing label and time-based indexing for coarse filtering, then applying a local sentence embedding model for semantic ranking over the filtered set. No external LLM calls, no persistent vector database, no changes to your Loki deployment.

It's best suited for exploratory debugging — when you know roughly where to look but not exactly what to search for. It doesn't replace LogQL, dashboards, or alerting. It fills the gap between "I know something is wrong with this service" and "I found the exact log lines that explain the problem."
