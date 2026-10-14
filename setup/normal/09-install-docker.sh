#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Run SETUP_DOCKER=yes setup/normal/00-install-kali-packages.sh first." >&2
  exit 1
fi

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

if command -v systemctl >/dev/null 2>&1; then
  $SUDO systemctl enable docker || true
  $SUDO systemctl start docker || $SUDO service docker start
else
  $SUDO service docker start
fi

$SUDO docker --version

if [ "${ADD_USER_TO_DOCKER_GROUP:-no}" = "yes" ]; then
  $SUDO usermod -aG docker "$USER"
  echo "Added $USER to docker group. Start a new shell or run: newgrp docker"
else
  echo "To run docker without sudo:"
  echo "  ADD_USER_TO_DOCKER_GROUP=yes $0"
fi

if [ "${RUN_HELLO_WORLD:-no}" = "yes" ]; then
  docker run hello-world
fi
