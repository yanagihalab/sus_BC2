#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_REPO="${TARGET_REPO:-$REPO_ROOT}"
VENV_DIR="${VENV_DIR:-$TARGET_REPO/venv}"
SETUP_SSH="${SETUP_SSH:-no}"
SETUP_VISUALIZER="${SETUP_VISUALIZER:-yes}"
SETUP_SIMBLOCK="${SETUP_SIMBLOCK:-no}"
SETUP_INJECTIVE="${SETUP_INJECTIVE:-no}"
SETUP_DOCKER="${SETUP_DOCKER:-no}"

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

if [ ! -f "$TARGET_REPO/requirements.txt" ]; then
  echo "requirements.txt was not found in TARGET_REPO: $TARGET_REPO" >&2
  exit 1
fi

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "Warning: this script is intended for Kali Linux on WSL." >&2
fi

"$SCRIPT_DIR/00-install-kali-packages.sh"

cd "$TARGET_REPO"
python3 -m venv "$VENV_DIR"
. "$VENV_DIR/bin/activate"
pip install -r requirements.txt

if [ "$SETUP_VISUALIZER" = "yes" ]; then
  "$SCRIPT_DIR/08-setup-proposer-visualizer.sh"
fi

if [ "$SETUP_SSH" = "yes" ]; then
  "$SCRIPT_DIR/02-setup-vscode-ssh.sh"
fi

if [ "$SETUP_SIMBLOCK" = "yes" ]; then
  "$SCRIPT_DIR/03-install-simblock.sh"
fi

if [ "$SETUP_INJECTIVE" = "yes" ]; then
  "$SCRIPT_DIR/04-install-injectived.sh"
fi

if [ "$SETUP_DOCKER" = "yes" ]; then
  "$SCRIPT_DIR/09-install-docker.sh"
fi

cat <<EOF
WSL / Kali Linux experiment environment is ready.

Repository:
  $TARGET_REPO

Python virtual environment:
  $VENV_DIR

Activate it with:
  cd "$TARGET_REPO"
  source "$VENV_DIR/bin/activate"

Optional setup flags:
  SETUP_SSH=yes $0
  SETUP_SIMBLOCK=yes $0
  SETUP_INJECTIVE=yes $0
  SETUP_DOCKER=yes $0
EOF
