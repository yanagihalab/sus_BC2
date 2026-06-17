#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
REPO_URL="${REPO_URL:-https://github.com/yanagihalab/sus_BC2}"
REPO_DIR="${REPO_DIR:-$WORKDIR/sus_BC2}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
else
  echo "Repository already exists: $REPO_DIR"
fi

cd "$REPO_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Python environment is ready: $REPO_DIR/venv"
