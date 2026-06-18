#!/usr/bin/env bash
set -euo pipefail

KEY_NAME="${KEY_NAME:-testwallet}"
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

cat <<EOF
Wallet is ready.

KEY_NAME=$KEY_NAME
CHAIN_ID=$CHAIN_ID
NODE=$NODE
GAS_PRICES=$GAS_PRICES
GAS=$GAS
MY_ADDR=$MY_ADDR

Load these values in the current shell:
  source scripts/injectived/load-env.sh

Check balance:
  injectived query bank balances "$MY_ADDR" --node="$NODE"
EOF
