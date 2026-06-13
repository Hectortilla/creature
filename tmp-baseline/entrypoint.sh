#!/usr/bin/env bash
set -euo pipefail

echo "::: [1/6] apt: psql + redis-cli + curl"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq postgresql-client redis-tools curl >/dev/null

echo "::: [2/6] install uv"
export HOME=/root
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.local/bin:$PATH"

echo "::: [3/6] backend deps (uv sync)"
cd /work/back
uv python install 3.12
uv sync --frozen

echo "::: [4/6] frontend deps (npm ci)"
cd /work/front
npm ci

echo "::: [5/6] generate linux screenshot baseline (game.e2e only)"
npm run test:e2e -- game.e2e.ts --update-snapshots

echo "::: [6/6] verify the fresh baseline matches on a clean run"
npm run test:e2e -- game.e2e.ts

echo "::: DONE — snapshots dir:"
ls -la e2e/game.e2e.ts-snapshots/
