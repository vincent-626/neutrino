.PHONY: dev dev-native dev-plugin run-backend \
        build-backend-plugin build-plugin dist test-backend

# ── Dev targets ──────────────────────────────────────────────────────────────

## Start full stack: Loki, Grafana, flog, promtail, neutrino backend (all Docker)
dev:
	docker compose -f deploy/docker-compose.yml up

## Start only Loki, flog, promtail in Docker (run backend + plugin natively)
dev-native:
	docker compose -f deploy/docker-compose.yml up loki flog promtail

## Watch-mode frontend build
dev-plugin:
	cd plugin && pnpm run dev

## Run Python backend locally with hot reload
run-backend:
	cd backend && PYTHONPATH=src uvicorn neutrino.main:app --host 0.0.0.0 --port 8400 --reload

# ── Build targets ─────────────────────────────────────────────────────────────

## Build Go plugin binaries for linux/amd64 and linux/arm64
build-backend-plugin:
	cd plugin && mage linux && mage linuxARM64

## Build TypeScript frontend
build-plugin:
	cd plugin && pnpm run build

## Full dist build: linux Go binary + frontend bundle
dist: build-backend-plugin build-plugin

# ── Test targets ─────────────────────────────────────────────────────────────

## Run Python backend tests
test-backend:
	cd backend && PYTHONPATH=src pytest tests/ -v
