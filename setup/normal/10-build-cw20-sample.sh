#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"

mkdir -p "$WORKDIR"

if [ ! -d "$CW_PLUS_DIR/.git" ]; then
  git clone https://github.com/CosmWasm/cw-plus.git "$CW_PLUS_DIR"
else
  echo "cw-plus repository already exists: $CW_PLUS_DIR"
fi

cd "$CW_PLUS_DIR"
ls contracts/cw20-base

docker run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0

ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
