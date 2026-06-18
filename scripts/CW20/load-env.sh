#!/usr/bin/env bash

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  cat <<'EOF'
This script must be sourced so the environment variables remain in the current shell.

Usage:
  source scripts/CW20/load-env.sh
EOF
  exit 1
fi

export KEY_NAME="${KEY_NAME:-testwallet}"
export CHAIN_ID="${CHAIN_ID:-injective-888}"
export NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
export GAS_PRICES="${GAS_PRICES:-500000000inj}"
export GAS="${GAS:-300000}"
export KEYRING_BACKEND="${KEYRING_BACKEND:-test}"
export WORKDIR="${WORKDIR:-$HOME/temp}"
export CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"
export WASM_PATH="${WASM_PATH:-$CW_PLUS_DIR/artifacts/cw20_base.wasm}"
export CODE_ID="${CODE_ID:-}"
export CONTRACT_ADDR="${CONTRACT_ADDR:-}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export CW20_SEND_AMOUNT="${CW20_SEND_AMOUNT:-1000000}"
export CW20_MINT_AMOUNT="${CW20_MINT_AMOUNT:-1000000}"

if command -v injectived >/dev/null 2>&1; then
  export SENDER_ADDR="${SENDER_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export SENDER_ADDR="${SENDER_ADDR:-}"
fi

export MY_ADDR="${MY_ADDR:-$SENDER_ADDR}"

cat <<EOF
CW20 environment loaded.
KEY_NAME=$KEY_NAME
CHAIN_ID=$CHAIN_ID
NODE=$NODE
GAS_PRICES=$GAS_PRICES
GAS=$GAS
WASM_PATH=$WASM_PATH
CODE_ID=$CODE_ID
CONTRACT_ADDR=$CONTRACT_ADDR
SENDER_ADDR=$SENDER_ADDR
RECIPIENT_ADDR=$RECIPIENT_ADDR
CW20_SEND_AMOUNT=$CW20_SEND_AMOUNT
CW20_MINT_AMOUNT=$CW20_MINT_AMOUNT
EOF
