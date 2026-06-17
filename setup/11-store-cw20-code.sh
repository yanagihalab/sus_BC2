#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$HOME/temp}"
CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"
WASM_PATH="${WASM_PATH:-$CW_PLUS_DIR/artifacts/cw20_base.wasm}"
KEY_NAME="${KEY_NAME:-testwallet}"
CHAIN_ID="${CHAIN_ID:-injective-888}"
NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
GAS_PRICES="${GAS_PRICES:-500000000inj}"
GAS="${GAS:-3000000}"
KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if [ ! -f "$WASM_PATH" ]; then
  echo "WASM file not found: $WASM_PATH" >&2
  echo "Run setup/10-build-cw20-sample.sh first." >&2
  exit 1
fi

if [ "${CONFIRM_TX:-no}" != "yes" ]; then
  cat <<EOF
This script stores CW20 WASM code on Injective.

WASM_PATH=$WASM_PATH
KEY_NAME=$KEY_NAME
CHAIN_ID=$CHAIN_ID
NODE=$NODE

Run with CONFIRM_TX=yes to execute.
EOF
  exit 1
fi

injectived tx wasm store "$WASM_PATH" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS"
