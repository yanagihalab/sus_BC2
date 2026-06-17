#!/usr/bin/env bash
set -euo pipefail

KEY_NAME="${KEY_NAME:-testwallet}"
CHAIN_ID="${CHAIN_ID:-injective-888}"
NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
GAS_PRICES="${GAS_PRICES:-500000000inj}"
GAS="${GAS:-200000}"
AMOUNT="${AMOUNT:-100000000inj}"
RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if [ -z "$RECIPIENT_ADDR" ]; then
  echo "Set RECIPIENT_ADDR before running this script." >&2
  echo "Example: RECIPIENT_ADDR=inj1... CONFIRM_SEND=yes $0" >&2
  exit 1
fi

if [ "${CONFIRM_SEND:-no}" != "yes" ]; then
  cat <<EOF
This script sends funds on Injective testnet.

KEY_NAME=$KEY_NAME
RECIPIENT_ADDR=$RECIPIENT_ADDR
AMOUNT=$AMOUNT
CHAIN_ID=$CHAIN_ID
NODE=$NODE

Run with CONFIRM_SEND=yes to execute.
EOF
  exit 1
fi

injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --broadcast-mode sync \
  -y
