.PHONY: dev dev-native dev-plugin run-backend \
        build-backend-plugin build-backend-plugin-all build-plugin dist test-backend

# Detect host architecture to match the Docker container platform.
# On Apple Silicon (arm64) Docker runs linux/arm64; on x86 it runs linux/amd64.
HOST_ARCH := $(shell uname -m)
ifeq ($(HOST_ARCH),arm64)
  MAGE_TARGET := linuxARM64
else
  MAGE_TARGET := linux
endif

# ── Dev targets ──────────────────────────────────────────────────────────────

## Build dist then start the full stack in Docker
dev: dist
	docker compose -f deploy/docker-compose.yml up

## Start only Loki, flog, promtail in Docker (run backend + plugin natively)
dev-native:
	docker compose -f deploy/docker-compose.yml up loki flog promtail

## Watch-mode frontend build
dev-plugin:
	cd plugin && pnpm run dev

## Run Python backend locally with hot reload
run-backend:
	cd backend && uv run uvicorn neutrino.main:app --host 0.0.0.0 --port 8400 --reload

# ── Build targets ─────────────────────────────────────────────────────────────

## Build Go plugin binary for the current host architecture only (faster)
build-backend-plugin:
	cd plugin && mage $(MAGE_TARGET)

## Build Go plugin binaries for both linux/amd64 and linux/arm64
build-backend-plugin-all:
	cd plugin && mage linux && mage linuxARM64

## Build TypeScript frontend
build-plugin:
	cd plugin && pnpm run build

## Full dist build: Go binary for host arch + frontend bundle
dist: build-backend-plugin build-plugin

# ── Test targets ─────────────────────────────────────────────────────────────

## Run Python backend tests
test-backend:
	cd backend && uv run pytest tests/ -v
