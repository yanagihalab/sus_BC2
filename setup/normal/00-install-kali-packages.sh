#!/usr/bin/env bash
set -euo pipefail

SETUP_DOCKER="${SETUP_DOCKER:-yes}"
SETUP_SSH="${SETUP_SSH:-no}"
for flag in SETUP_DOCKER SETUP_SSH; do
  case "${!flag}" in
    yes|no) ;;
    *)
      echo "$flag must be yes or no." >&2
      exit 1
      ;;
  esac
done

PACKAGES=(
  python3-pip python3-venv openjdk-11-jdk
  unzip npm jq git curl nodejs
  bash ca-certificates openssh-client wget
)
if [ "$SETUP_DOCKER" = "yes" ]; then
  PACKAGES+=(docker.io)
fi
if [ "$SETUP_SSH" = "yes" ]; then
  PACKAGES+=(openssh-server)
fi

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
elif [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  echo "sudo command is required when not running as root." >&2
  exit 1
fi

run_apt() {
  local stage="$1"
  local line="${BASH_LINENO[0]}"
  shift

  printf '==> %s\n' "$stage"
  if "$@"; then
    return 0
  else
    local status=$?
    printf 'APT stage failed: %s\nScript: %s:%s\nCommand:' \
      "$stage" "${BASH_SOURCE[0]}" "$line" >&2
    printf ' %q' "$@" >&2
    printf '\nExit code: %s\n' "$status" >&2
    exit "$status"
  fi
}

run_apt "Updating APT package indexes" \
  $SUDO apt-get --error-on=any -o Acquire::Retries=5 update
run_apt "Upgrading installed packages" \
  $SUDO apt-get -o Acquire::Retries=5 --with-new-pkgs upgrade -y
run_apt "Installing development dependencies" \
  $SUDO apt-get -o Acquire::Retries=5 install -y \
  "${PACKAGES[@]}"

NODE_VERSION="$(node --version)"
NODE_MAJOR="${NODE_VERSION#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
if [[ ! "$NODE_MAJOR" =~ ^[0-9]+$ ]] || [ "$NODE_MAJOR" -lt 20 ]; then
  echo "Node.js 20 or later is required; installed version: $NODE_VERSION" >&2
  echo "Check the configured Kali repository and the available Node.js version." >&2
  exit 1
fi

python3 --version
git --version
java -version
node --version
npm --version
jq --version
echo "Installed basic packages."
