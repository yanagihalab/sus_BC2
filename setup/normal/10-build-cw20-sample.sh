#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed. Run setup/normal/09-install-docker.sh first." >&2
  exit 1
fi

DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
    DOCKER=(sudo docker)
  else
    echo "Docker Engine is unavailable. Start Docker and check Docker socket permissions." >&2
    exit 1
  fi
fi

mkdir -p "$WORKDIR"

if [ ! -d "$CW_PLUS_DIR/.git" ]; then
  git clone https://github.com/CosmWasm/cw-plus.git "$CW_PLUS_DIR"
else
  echo "cw-plus repository already exists: $CW_PLUS_DIR"
fi

cd "$CW_PLUS_DIR"
ls contracts/cw20-base

"${DOCKER[@]}" run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0

ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
