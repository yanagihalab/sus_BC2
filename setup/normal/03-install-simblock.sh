#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
SIMBLOCK_DIR="${SIMBLOCK_DIR:-$WORKDIR/simblock}"

for dependency in git unzip; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "$dependency is required. Run setup/normal/00-install-kali-packages.sh first." >&2
    exit 1
  fi
done

mkdir -p "$WORKDIR"

if [ ! -d "$SIMBLOCK_DIR/.git" ]; then
  git clone https://github.com/dsg-titech/simblock "$SIMBLOCK_DIR"
else
  echo "SimBlock repository already exists: $SIMBLOCK_DIR"
fi

is_java11_jdk() {
  local jdk_dir="$1"
  local version
  [ -n "$jdk_dir" ] && [ -x "$jdk_dir/bin/java" ] && [ -x "$jdk_dir/bin/javac" ] || return 1
  version="$("$jdk_dir/bin/java" -version 2>&1)" || return 1
  [[ "$version" == *'version "11.'* || "$version" == *'version "11"'* ]]
}

if ! is_java11_jdk "${JAVA_HOME:-}"; then
  JAVA_HOME=""
  while IFS= read -r candidate; do
    if is_java11_jdk "$candidate"; then
      JAVA_HOME="$candidate"
      break
    fi
  done < <(find /usr/lib/jvm -maxdepth 1 -type d -name 'java-11-openjdk-*' | sort)
fi

if [ -z "$JAVA_HOME" ]; then
  echo "A Java 11 JDK was not found. Run setup/normal/00-install-kali-packages.sh first and check openjdk-11-jdk under /usr/lib/jvm." >&2
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
