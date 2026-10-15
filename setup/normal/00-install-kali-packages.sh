#!/usr/bin/env bash
set -euo pipefail

SETUP_DOCKER="${SETUP_DOCKER:-yes}"
SETUP_SSH="${SETUP_SSH:-no}"
APT_HTTP_MAX_ATTEMPTS="${APT_HTTP_MAX_ATTEMPTS:-3}"
APT_HTTP_RETRY_DELAY="${APT_HTTP_RETRY_DELAY:-10}"
for flag in SETUP_DOCKER SETUP_SSH; do
  case "${!flag}" in
    yes|no) ;;
    *)
      echo "$flag must be yes or no." >&2
      exit 1
      ;;
  esac
done
if [[ ! "$APT_HTTP_MAX_ATTEMPTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "APT_HTTP_MAX_ATTEMPTS must be a positive integer." >&2
  exit 1
fi
if [[ ! "$APT_HTTP_RETRY_DELAY" =~ ^[0-9]+$ ]]; then
  echo "APT_HTTP_RETRY_DELAY must be a non-negative integer." >&2
  exit 1
fi

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

apt_failure() {
  local stage="$1"
  local line="$2"
  local status="$3"
  shift 3
  printf 'APT stage failed: %s\nScript: %s:%s\nCommand:' \
    "$stage" "${BASH_SOURCE[0]}" "$line" >&2
  printf ' %q' "$@" >&2
  printf '\nExit code: %s\n' "$status" >&2
  exit "$status"
}

run_apt() {
  local stage="$1"
  local line="${BASH_LINENO[0]}"
  shift

  printf '==> %s\n' "$stage"
  if "$@"; then
    return 0
  else
    local status=$?
    apt_failure "$stage" "$line" "$status" "$@"
  fi
}

retryable_http_fetch_failure() {
  local error_line
  local found_http_error=no
  while IFS= read -r error_line || [ -n "$error_line" ]; do
    case "$error_line" in
      'E: Failed to fetch '*)
        if [[ "$error_line" =~ [[:space:]](500|502|503|504)[[:space:]] ]]; then
          found_http_error=yes
        else
          return 1
        fi
        ;;
      'E: Unable to fetch some archives'*) ;;
      E:*) return 1 ;;
    esac
  done < "$1"
  [ "$found_http_error" = yes ]
}

download_apt_packages() {
  local stage="$1"
  local line="${BASH_LINENO[0]}"
  local attempt=1
  local status
  local pipeline_status
  shift

  APT_FETCH_LOG="$(mktemp)"
  trap 'rm -f -- "$APT_FETCH_LOG"' EXIT
  while true; do
    printf '==> %s (attempt %s/%s)\n' "$stage" "$attempt" "$APT_HTTP_MAX_ATTEMPTS"
    if LC_ALL=C "$@" 2>&1 | tee "$APT_FETCH_LOG"; then
      return 0
    else
      pipeline_status=("${PIPESTATUS[@]}")
      status="${pipeline_status[0]}"
      if [ "$status" -eq 0 ]; then
        status="${pipeline_status[1]}"
      fi
    fi
    if [ "$status" -eq 100 ] && [ "${pipeline_status[1]}" -eq 0 ] && \
       retryable_http_fetch_failure "$APT_FETCH_LOG"; then
      if [ "$attempt" -lt "$APT_HTTP_MAX_ATTEMPTS" ]; then
        printf 'HTTP download error; retrying in %s seconds. Cached packages are kept.\n' \
          "$APT_HTTP_RETRY_DELAY" >&2
        sleep "$APT_HTTP_RETRY_DELAY"
        attempt=$((attempt + 1))
        continue
      fi
      printf 'HTTP download retries exhausted after %s attempts. Check the configured Kali mirror or retry later.\n' \
        "$attempt" >&2
    fi
    apt_failure "$stage" "$line" "$status" "$@"
  done
}

run_apt "Updating APT package indexes" \
  $SUDO apt-get --error-on=any -o Acquire::Retries=5 update
run_apt "Upgrading installed packages" \
  $SUDO apt-get -o Acquire::Retries=5 --with-new-pkgs upgrade -y
download_apt_packages "Downloading development dependencies" \
  $SUDO apt-get -o Acquire::Retries=5 --download-only install -y \
  "${PACKAGES[@]}"
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
