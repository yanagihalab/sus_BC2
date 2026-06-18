#!/usr/bin/env bash

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  cat <<'EOF'
This script must be sourced so the environment variables remain in the current shell.

Usage:
  source scripts/tokenfactory/load-env.sh
EOF
  exit 1
fi

export KEY_NAME="${KEY_NAME:-testwallet}"
export CHAIN_ID="${CHAIN_ID:-injective-888}"
export NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
export GAS_PRICES="${GAS_PRICES:-500000000inj}"
export GAS="${GAS:-300000}"
export SUBDENOM="${SUBDENOM:-mtk}"
export KEYRING_BACKEND="${KEYRING_BACKEND:-test}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export SEND_AMOUNT="${SEND_AMOUNT:-1000000}"

if command -v injectived >/dev/null 2>&1; then
  export CREATOR_ADDR="${CREATOR_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export CREATOR_ADDR="${CREATOR_ADDR:-}"
fi

if [ -n "$CREATOR_ADDR" ]; then
  export DENOM="${DENOM:-factory/${CREATOR_ADDR}/${SUBDENOM}}"
else
  export DENOM="${DENOM:-}"
fi

cat <<EOF
TokenFactory environment loaded.
KEY_NAME=$KEY_NAME
CHAIN_ID=$CHAIN_ID
NODE=$NODE
GAS_PRICES=$GAS_PRICES
GAS=$GAS
SUBDENOM=$SUBDENOM
CREATOR_ADDR=$CREATOR_ADDR
DENOM=$DENOM
RECIPIENT_ADDR=$RECIPIENT_ADDR
SEND_AMOUNT=$SEND_AMOUNT
EOF
