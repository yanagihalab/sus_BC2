#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-2222}"

if ! command -v sshd >/dev/null 2>&1 && [ ! -x /usr/sbin/sshd ]; then
  echo "OpenSSH server is required. Run SETUP_SSH=yes setup/normal/00-install-kali-packages.sh first." >&2
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

SSHD_CONFIG="/etc/ssh/sshd_config"
$SUDO cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

set_config() {
  local key="$1"
  local value="$2"

  if $SUDO grep -Eq "^[#[:space:]]*${key}[[:space:]]+" "$SSHD_CONFIG"; then
    $SUDO sed -i -E "s|^[#[:space:]]*${key}[[:space:]]+.*|${key} ${value}|" "$SSHD_CONFIG"
  else
    printf '%s %s\n' "$key" "$value" | $SUDO tee -a "$SSHD_CONFIG" >/dev/null
  fi
}

set_config "Port" "$PORT"
set_config "PasswordAuthentication" "yes"
set_config "PermitRootLogin" "no"

$SUDO service ssh restart

cat <<EOF
SSH server is ready.

From Windows PowerShell, test with:
  ssh $(whoami)@127.0.0.1 -p $PORT

VS Code Remote - SSH config example:
  Host kali-linux
    HostName 127.0.0.1
    User $(whoami)
    Port $PORT
EOF
