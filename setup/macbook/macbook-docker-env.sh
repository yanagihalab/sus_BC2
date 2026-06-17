#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-sus-bc2-kali-env}"
RUN_VERIFY="${RUN_VERIFY:-yes}"
RUN_AMD64_INJECTIVE_CHECK="${RUN_AMD64_INJECTIVE_CHECK:-no}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command is not installed. Start Docker Desktop first." >&2
  exit 1
fi

docker info >/dev/null

docker build -t "$IMAGE_NAME" -f - /tmp <<'DOCKERFILE'
FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update \
  && apt install -y \
    bash \
    ca-certificates \
    curl \
    git \
    jq \
    nodejs \
    npm \
    openjdk-11-jdk \
    openssh-client \
    python3-pip \
    python3-venv \
    unzip \
    wget \
  && apt clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /work
DOCKERFILE

echo "Built Docker image: $IMAGE_NAME"

if [ "$RUN_VERIFY" = "yes" ]; then
  docker run --rm \
    -v "$REPO_ROOT:/work" \
    -w /work \
    "$IMAGE_NAME" \
    bash -lc '
      set -euo pipefail

      echo "[1/5] Checking shell syntax"
      for f in setup/normal/*.sh setup/macbook/*.sh; do
        bash -n "$f"
      done

      echo "[2/5] Checking Python environment"
      python3 -m venv /tmp/sus-bc2-venv
      . /tmp/sus-bc2-venv/bin/activate
      pip install -r requirements.txt

      echo "[3/5] Checking MTK helper usage"
      ./setup/macbook/07-tokenfactory-mtk.sh help >/tmp/mtk-help.txt
      grep -q "Usage:" /tmp/mtk-help.txt

      echo "[4/5] Checking bank send safety guard"
      if ./setup/macbook/06-bank-send.sh >/tmp/bank-send.txt 2>&1; then
        echo "bank send guard failed: script succeeded without RECIPIENT_ADDR" >&2
        exit 1
      fi
      grep -q "Set RECIPIENT_ADDR" /tmp/bank-send.txt

      echo "[5/5] Checking CW20 store safety guard"
      if CONFIRM_TX=yes ./setup/macbook/11-store-cw20-code.sh >/tmp/cw20-store.txt 2>&1; then
        echo "cw20 store guard failed: script succeeded without WASM file" >&2
        exit 1
      fi
      grep -q "WASM file not found" /tmp/cw20-store.txt

      echo "MacBook Docker environment verification completed."
    '
fi

if [ "$RUN_AMD64_INJECTIVE_CHECK" = "yes" ]; then
  docker run --rm --platform linux/amd64 \
    -v "$REPO_ROOT:/work" \
    -w /work \
    kalilinux/kali-rolling \
    bash -lc 'WORKDIR=/tmp ./setup/macbook/04-install-injectived.sh'
fi

cat <<EOF
MacBook Docker environment is ready.

Start an interactive Kali container with:
  docker run --rm -it -v "$REPO_ROOT:/work" -w /work $IMAGE_NAME bash

Optional amd64 injectived check:
  RUN_AMD64_INJECTIVE_CHECK=yes $0
EOF
