#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="${APP_DIR:-$REPO_ROOT/Day1/Proposer-visualizer}"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js and npm are required. Run setup/normal/00-install-kali-packages.sh first." >&2
  exit 1
fi

NODE_VERSION="$(node --version)"
NODE_MAJOR="${NODE_VERSION#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
if [[ ! "$NODE_MAJOR" =~ ^[0-9]+$ ]] || [ "$NODE_MAJOR" -lt 20 ]; then
  echo "Node.js 20 or later is required; installed version: $NODE_VERSION" >&2
  echo "Run setup/normal/00-install-kali-packages.sh first." >&2
  exit 1
fi

cd "$APP_DIR"

if [ "${RESET_NODE_MODULES:-no}" = "yes" ]; then
  rm -rf node_modules package-lock.json
fi

npm install

if [ "${RUN_VISUALIZER:-no}" = "yes" ]; then
  npm run start
else
  echo "Dependencies installed. To start the visualizer:"
  echo "  cd $APP_DIR && npm run start"
fi
