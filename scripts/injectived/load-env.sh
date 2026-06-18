#!/usr/bin/env bash

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  cat <<'EOF'
This script must be sourced so the environment variables remain in the current shell.

Usage:
  source scripts/injectived/load-env.sh
EOF
  exit 1
fi

export KEY_NAME="${KEY_NAME:-testwallet}"
export CHAIN_ID="${CHAIN_ID:-injective-888}"
export NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
export GAS_PRICES="${GAS_PRICES:-500000000inj}"
export GAS="${GAS:-1000000}"
export BANK_SEND_GAS="${BANK_SEND_GAS:-200000}"
export AMOUNT="${AMOUNT:-100000000inj}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if command -v injectived >/dev/null 2>&1; then
  export MY_ADDR="${MY_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export MY_ADDR="${MY_ADDR:-}"
fi

export ADDR="${ADDR:-$MY_ADDR}"

cat <<EOF
injectived environment loaded.
KEY_NAME=$KEY_NAME
CHAIN_ID=$CHAIN_ID
NODE=$NODE
GAS_PRICES=$GAS_PRICES
GAS=$GAS
BANK_SEND_GAS=$BANK_SEND_GAS
AMOUNT=$AMOUNT
RECIPIENT_ADDR=$RECIPIENT_ADDR
MY_ADDR=$MY_ADDR
EOF
