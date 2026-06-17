#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

$SUDO apt update
$SUDO apt install -y wget unzip

mkdir -p "$WORKDIR"
cd "$WORKDIR"

wget -O linux-amd64.zip https://github.com/InjectiveFoundation/injective-core/releases/latest/download/linux-amd64.zip
unzip -o linux-amd64.zip
chmod +x injectived
$SUDO mv injectived /usr/local/bin/

if [ -f libwasmvm.x86_64.so ]; then
  $SUDO mv libwasmvm.x86_64.so /usr/lib/
  $SUDO ldconfig
fi

injectived version
