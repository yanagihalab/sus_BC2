#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [key-name]

The argument overrides KEY_NAME. If both are unset, the key name is testwallet.
KEYRING_BACKEND defaults to test.

Examples:
  $0 testwallet
  $0 receiverwallet
EOF
}

if [ "$#" -gt 1 ]; then
  usage >&2
  exit 2
fi
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ "$#" -eq 1 ]; then
  KEY_NAME="$1"
else
  KEY_NAME="${KEY_NAME-testwallet}"
fi
if [ -z "${KEY_NAME//[[:space:]]/}" ]; then
  echo "KEY_NAME is empty. Specify a key name, for example: $0 receiverwallet" >&2
  exit 2
fi
CHAIN_ID="${CHAIN_ID:-injective-888}"
NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
GAS_PRICES="${GAS_PRICES:-500000000inj}"
GAS="${GAS:-1000000}"
KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if ! command -v injectived >/dev/null 2>&1; then
  echo "injectived is not installed. Run scripts/injectived/install-injectived.sh first." >&2
  exit 1
fi

if ! injectived keys show "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" >/dev/null 2>&1; then
  injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
else
  echo "Wallet already exists: $KEY_NAME"
fi

MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
if [ -z "${MY_ADDR//[[:space:]]/}" ]; then
  echo "Could not obtain an address for KEY_NAME=$KEY_NAME (KEYRING_BACKEND=$KEYRING_BACKEND)." >&2
  exit 1
fi

cat <<EOF
Wallet is ready.

KEY_NAME=$KEY_NAME
KEYRING_BACKEND=$KEYRING_BACKEND
CHAIN_ID=$CHAIN_ID
NODE=$NODE
GAS_PRICES=$GAS_PRICES
GAS=$GAS
MY_ADDR=$MY_ADDR

This script cannot change the calling shell.
To load this wallet in the current Bash session, run:
EOF
printf '  export KEY_NAME=%q KEYRING_BACKEND=%q\n' "$KEY_NAME" "$KEYRING_BACKEND"
printf '  export CHAIN_ID=%q NODE=%q GAS_PRICES=%q GAS=%q\n' "$CHAIN_ID" "$NODE" "$GAS_PRICES" "$GAS"
printf '  export MY_ADDR=%q ADDR=%q\n' "$MY_ADDR" "$MY_ADDR"
cat <<EOF
  source scripts/injectived/load-env.sh

Check balance:
  injectived query bank balances "$MY_ADDR" --node="$NODE"
EOF
