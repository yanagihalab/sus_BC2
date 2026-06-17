#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE="${IMAGE:-kalilinux/kali-rolling}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command is not installed." >&2
  exit 1
fi

docker run --rm \
  -v "$REPO_ROOT:/work" \
  -w /work \
  "$IMAGE" \
  bash -lc '
    set -euo pipefail

    echo "[1/5] Checking README and setup directory"
    test -f README.md
    test -d setup/normal
    test -d setup/macbook

    echo "[2/5] Checking shell syntax"
    for f in setup/normal/*.sh setup/macbook/*.sh; do
      bash -n "$f"
    done

    echo "[3/5] Checking MTK helper usage"
    ./setup/normal/07-tokenfactory-mtk.sh help >/tmp/mtk-help.txt
    grep -q "Usage:" /tmp/mtk-help.txt

    echo "[4/5] Checking bank send safety guard"
    if ./setup/normal/06-bank-send.sh >/tmp/bank-send.txt 2>&1; then
      echo "bank send guard failed: script succeeded without RECIPIENT_ADDR" >&2
      exit 1
    fi
    grep -q "Set RECIPIENT_ADDR" /tmp/bank-send.txt

    echo "[5/5] Checking CW20 store safety guard"
    if CONFIRM_TX=yes ./setup/normal/11-store-cw20-code.sh >/tmp/cw20-store.txt 2>&1; then
      echo "cw20 store guard failed: script succeeded without WASM file" >&2
      exit 1
    fi
    grep -q "WASM file not found" /tmp/cw20-store.txt

    echo "Docker verification completed."
  '
