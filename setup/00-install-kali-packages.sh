#!/usr/bin/env bash
set -euo pipefail

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

$SUDO apt update
$SUDO apt upgrade -y
$SUDO apt install -y \
  python3-pip \
  python3-venv \
  openjdk-11-jdk \
  unzip \
  npm \
  jq \
  git \
  curl \
  nodejs

echo "Installed basic packages."
python3 --version
git --version
java -version
node --version
npm --version
jq --version
