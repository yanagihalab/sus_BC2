#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_REPO="${TARGET_REPO:-$REPO_ROOT}"
SETUP_SSH="${SETUP_SSH:-no}"
SETUP_VISUALIZER="${SETUP_VISUALIZER:-yes}"
SETUP_SIMBLOCK="${SETUP_SIMBLOCK:-yes}"
SETUP_INJECTIVE="${SETUP_INJECTIVE:-yes}"
SETUP_DOCKER="${SETUP_DOCKER:-yes}"
SETUP_CW20="${SETUP_CW20:-yes}"

for flag in SETUP_SSH SETUP_VISUALIZER SETUP_SIMBLOCK SETUP_INJECTIVE SETUP_DOCKER SETUP_CW20; do
  case "${!flag}" in
    yes|no) ;;
    *)
      echo "$flag must be yes or no." >&2
      exit 1
      ;;
  esac
done

if [ "$SETUP_CW20" = "yes" ] && [ "$SETUP_DOCKER" != "yes" ]; then
  echo "SETUP_CW20=yes requires SETUP_DOCKER=yes. To skip Docker, also set SETUP_CW20=no." >&2
  exit 1
fi

if [ "$SETUP_INJECTIVE" = "yes" ]; then
  ARCH="$(uname -m)"
  if [ "$ARCH" != "x86_64" ]; then
    echo "injectived installation is unsupported on $ARCH: the installer requires Linux x86_64." >&2
    echo "Set SETUP_INJECTIVE=no to build the remaining environment without injectived." >&2
    exit 1
  fi
fi

TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"
if [ ! -f "$TARGET_REPO/requirements.txt" ]; then
  echo "requirements.txt was not found in TARGET_REPO: $TARGET_REPO" >&2
  exit 1
fi

WORKDIR="${WORKDIR:-$(dirname "$TARGET_REPO")}"
VENV_DIR="${VENV_DIR:-$TARGET_REPO/venv}"
APP_DIR="${APP_DIR:-$TARGET_REPO/Day1/Proposer-visualizer}"
case "$VENV_DIR" in
  /*) ;;
  *) VENV_DIR="$TARGET_REPO/$VENV_DIR" ;;
esac
case "$APP_DIR" in
  /*) ;;
  *) APP_DIR="$TARGET_REPO/$APP_DIR" ;;
esac
if [ "$SETUP_VISUALIZER" = "yes" ] && [ ! -f "$APP_DIR/package.json" ]; then
  echo "package.json was not found in APP_DIR: $APP_DIR" >&2
  exit 1
fi

mkdir -p "$WORKDIR"
WORKDIR="$(cd "$WORKDIR" && pwd)"
export TARGET_REPO WORKDIR VENV_DIR APP_DIR

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "Warning: this script is intended for Kali Linux on WSL." >&2
fi

run_setup() {
  local description="$1"
  shift
  printf '\n==> %s\n' "$description"
  "$@"
}

run_setup "Installing Kali packages" \
  env SETUP_DOCKER="$SETUP_DOCKER" SETUP_SSH="$SETUP_SSH" \
  "$SCRIPT_DIR/00-install-kali-packages.sh"

cd "$TARGET_REPO"
printf '\n==> Creating the Python virtual environment\n'
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install -r "$TARGET_REPO/requirements.txt"

if [ "$SETUP_VISUALIZER" = "yes" ]; then
  run_setup "Installing Proposer Visualizer dependencies" \
    env RUN_VISUALIZER=no "$SCRIPT_DIR/08-setup-proposer-visualizer.sh"
fi

if [ "$SETUP_SSH" = "yes" ]; then
  run_setup "Configuring the optional SSH server" "$SCRIPT_DIR/02-setup-vscode-ssh.sh"
fi

if [ "$SETUP_SIMBLOCK" = "yes" ]; then
  run_setup "Installing and building SimBlock" \
    env RUN_SIMBLOCK=no "$SCRIPT_DIR/03-install-simblock.sh"
fi

if [ "$SETUP_INJECTIVE" = "yes" ]; then
  run_setup "Installing injectived" "$SCRIPT_DIR/04-install-injectived.sh"
fi

if [ "$SETUP_DOCKER" = "yes" ]; then
  run_setup "Starting Docker Engine" \
    env RUN_HELLO_WORLD=no "$SCRIPT_DIR/09-install-docker.sh"
fi

if [ "$SETUP_CW20" = "yes" ]; then
  run_setup "Building the CW20 sample WASM" "$SCRIPT_DIR/10-build-cw20-sample.sh"
fi

cat <<EOF
WSL / Kali Linux experiment environment is ready.

Repository:
  $TARGET_REPO

Python virtual environment:
  $VENV_DIR

External repositories and downloads:
  $WORKDIR

Activate it with:
  cd "$TARGET_REPO"
  source "$VENV_DIR/bin/activate"

Optional SSH setup:
  SETUP_SSH=yes $0

Skip selected build components:
  SETUP_VISUALIZER=no $0
  SETUP_SIMBLOCK=no $0
  SETUP_INJECTIVE=no $0
  SETUP_CW20=no $0
  SETUP_DOCKER=no SETUP_CW20=no $0
EOF
