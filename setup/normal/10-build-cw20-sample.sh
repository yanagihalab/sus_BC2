#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed. Run SETUP_DOCKER=yes setup/normal/00-install-kali-packages.sh first, then setup/normal/09-install-docker.sh to start Docker." >&2
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
  git clone --depth 1 https://github.com/CosmWasm/cw-plus.git "$CW_PLUS_DIR"
else
  echo "cw-plus repository already exists: $CW_PLUS_DIR"
fi

cd "$CW_PLUS_DIR"
if [ ! -f contracts/cw20-base/Cargo.toml ]; then
  echo "CW20 sample was not found: $CW_PLUS_DIR/contracts/cw20-base/Cargo.toml" >&2
  exit 1
fi

echo "Building only cw20-base; removing old WASM artifacts and checksums."
"${DOCKER[@]}" run --rm \
  --entrypoint /bin/sh \
  -v "$(pwd)":/code \
  --mount type=volume,source=cw20_base_cache,target=/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0 \
  -c '
    set -eu
    rm -f artifacts/*.wasm artifacts/checksums.txt
    exec /usr/local/bin/optimize.sh ./contracts/cw20-base
  '

if [ ! -s artifacts/cw20_base.wasm ]; then
  echo "CW20 build did not produce a non-empty WASM file: $CW_PLUS_DIR/artifacts/cw20_base.wasm" >&2
  exit 1
fi

ls -lh artifacts/cw20_base.wasm
ls -lh artifacts/checksums.txt
