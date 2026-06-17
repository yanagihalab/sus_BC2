#!/usr/bin/env bash
set -euo pipefail

KEY_NAME="${KEY_NAME:-testwallet}"
CHAIN_ID="${CHAIN_ID:-injective-888}"
NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
GAS_PRICES="${GAS_PRICES:-500000000inj}"
GAS="${GAS:-1000000}"

if ! command -v injectived >/dev/null 2>&1; then
  echo "injectived is not installed. Run setup/normal/04-install-injectived.sh first." >&2
  exit 1
fi

if ! injectived keys show "$KEY_NAME" --keyring-backend test >/dev/null 2>&1; then
  injectived keys add "$KEY_NAME" --keyring-backend test
else
  echo "Wallet already exists: $KEY_NAME"
fi

MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend test)"

cat <<EOF
Wallet is ready.

export CHAIN_ID=$CHAIN_ID
export NODE=$NODE
export GAS_PRICES=$GAS_PRICES
export GAS=$GAS
export KEY_NAME=$KEY_NAME
export MY_ADDR=$MY_ADDR

Check balance:
  injectived query bank balances "$MY_ADDR" --node="$NODE"
EOF
