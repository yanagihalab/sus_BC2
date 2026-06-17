#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-help}"
KEY_NAME="${KEY_NAME:-testwallet}"
CHAIN_ID="${CHAIN_ID:-injective-888}"
NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
GAS_PRICES="${GAS_PRICES:-500000000inj}"
GAS="${GAS:-300000}"
SUBDENOM="${SUBDENOM:-mtk}"
KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

usage() {
  cat <<EOF
Usage: $0 <action>

Actions:
  env             Print TokenFactory environment values.
  create-denom    Create denom for SUBDENOM.
  set-metadata    Set token metadata.
  mint            Mint MINT_AMOUNT to creator.
  balance         Query creator balance.
  send            Send SEND_AMOUNT to RECIPIENT_ADDR.

Required confirmation for write actions:
  CONFIRM_TX=yes

Examples:
  $0 env
  CONFIRM_TX=yes $0 create-denom
  MINT_AMOUNT=1000000000 CONFIRM_TX=yes $0 mint
  RECIPIENT_ADDR=inj1... SEND_AMOUNT=1000000 CONFIRM_TX=yes $0 send
EOF
}

creator_addr() {
  injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND"
}

require_confirm() {
  if [ "${CONFIRM_TX:-no}" != "yes" ]; then
    echo "This action writes to the chain. Run with CONFIRM_TX=yes to execute." >&2
    exit 1
  fi
}

case "$ACTION" in
  env)
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    cat <<EOF
export KEY_NAME=$KEY_NAME
export CHAIN_ID=$CHAIN_ID
export NODE=$NODE
export GAS_PRICES=$GAS_PRICES
export GAS=$GAS
export SUBDENOM=$SUBDENOM
export CREATOR_ADDR=$CREATOR_ADDR
export DENOM=$DENOM
EOF
    ;;
  create-denom)
    require_confirm
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    injectived tx tokenfactory create-denom \
      "$SUBDENOM" \
      "My Token" \
      "MTK" \
      6 \
      --from="$KEY_NAME" \
      --keyring-backend "$KEYRING_BACKEND" \
      --chain-id="$CHAIN_ID" \
      --node="$NODE" \
      --gas-prices="$GAS_PRICES" \
      --gas="$GAS" \
      -y
    ;;
  set-metadata)
    require_confirm
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    injectived tx tokenfactory set-denom-metadata \
      "My Token Description" \
      "$DENOM" \
      "MTK" \
      "My Token" \
      "MTK" \
      "" \
      "" \
      "[{\"denom\":\"$DENOM\",\"exponent\":0,\"aliases\":[]},{\"denom\":\"MTK\",\"exponent\":6,\"aliases\":[]}]" \
      10 \
      6 \
      --from="$KEY_NAME" \
      --keyring-backend "$KEYRING_BACKEND" \
      --chain-id="$CHAIN_ID" \
      --node="$NODE" \
      --gas-prices="$GAS_PRICES" \
      --gas="$GAS" \
      -y
    ;;
  mint)
    require_confirm
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    MINT_AMOUNT="${MINT_AMOUNT:-1000000000}"
    injectived tx tokenfactory mint \
      "${MINT_AMOUNT}${DENOM}" \
      "$CREATOR_ADDR" \
      --from="$KEY_NAME" \
      --keyring-backend "$KEYRING_BACKEND" \
      --chain-id="$CHAIN_ID" \
      --node="$NODE" \
      --gas-prices="$GAS_PRICES" \
      --gas="$GAS" \
      -y
    ;;
  balance)
    CREATOR_ADDR="$(creator_addr)"
    injectived query bank balances "$CREATOR_ADDR" \
      --node="$NODE" \
      --chain-id="$CHAIN_ID" \
      -o json | jq
    ;;
  send)
    require_confirm
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
    SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
    if [ -z "$RECIPIENT_ADDR" ]; then
      echo "Set RECIPIENT_ADDR before running send." >&2
      exit 1
    fi
    injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "${SEND_AMOUNT}${DENOM}" \
      --from="$KEY_NAME" \
      --keyring-backend "$KEYRING_BACKEND" \
      --chain-id="$CHAIN_ID" \
      --node="$NODE" \
      --gas-prices="$GAS_PRICES" \
      --gas="$GAS" \
      -y
    ;;
  help|*)
    usage
    ;;
esac
