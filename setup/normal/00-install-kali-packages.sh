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

NODE_VERSION="$(node --version)"
NODE_MAJOR="${NODE_VERSION#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
if [[ ! "$NODE_MAJOR" =~ ^[0-9]+$ ]] || [ "$NODE_MAJOR" -lt 20 ]; then
  echo "Node.js 20 or later is required; installed version: $NODE_VERSION" >&2
  echo "Check that apt uses the current Kali rolling repository." >&2
  exit 1
fi

echo "Installed basic packages."
python3 --version
git --version
java -version
node --version
npm --version
jq --version
