#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
python3 -m compileall -q vast scripts tests
sh -n docker/tunnel/start.sh vast/start.sh scripts/check.sh
if [ -n "${COMPOSE_BINARY:-}" ]; then
    "$COMPOSE_BINARY" --env-file .env.example config --no-env-resolution --quiet
elif command -v docker >/dev/null 2>&1; then
    # Configuration only; no build, deploy or live mutation.
    docker compose --env-file .env.example config --no-env-resolution --quiet
else
    echo "SKIP: Docker Compose validation (Docker is unavailable)"
fi
