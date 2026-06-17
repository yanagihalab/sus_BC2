#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
SIMBLOCK_DIR="${SIMBLOCK_DIR:-$WORKDIR/simblock}"

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

$SUDO apt update
$SUDO apt install -y openjdk-11-jdk unzip git

mkdir -p "$WORKDIR"

if [ ! -d "$SIMBLOCK_DIR/.git" ]; then
  git clone https://github.com/dsg-titech/simblock "$SIMBLOCK_DIR"
else
  echo "SimBlock repository already exists: $SIMBLOCK_DIR"
fi

if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME="$(find /usr/lib/jvm -maxdepth 1 -type d -name 'java-11-openjdk-*' | sort | head -n 1)"
fi

if [ -z "$JAVA_HOME" ] || [ ! -d "$JAVA_HOME" ]; then
  echo "Java 11 installation directory was not found under /usr/lib/jvm." >&2
  exit 1
fi

export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"

cd "$SIMBLOCK_DIR"
chmod +x gradlew
./gradlew clean
./gradlew build

if [ "${RUN_SIMBLOCK:-no}" = "yes" ]; then
  ./gradlew :simulator:run
else
  echo "Build completed. To run SimBlock now, execute:"
  echo "  cd $SIMBLOCK_DIR && ./gradlew :simulator:run"
fi
