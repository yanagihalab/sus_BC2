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
TOKEN_NAME="${TOKEN_NAME:-My Token}"
TOKEN_SYMBOL="${TOKEN_SYMBOL:-MTK}"
TOKEN_DESCRIPTION="${TOKEN_DESCRIPTION-My Token Description}"
TOKEN_DISPLAY="${TOKEN_DISPLAY:-}"
TOKEN_DECIMALS="${TOKEN_DECIMALS:-6}"
TOKEN_URI="${TOKEN_URI:-}"
TOKEN_URI_HASH="${TOKEN_URI_HASH:-}"

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

Metadata environment variables:
  TOKEN_NAME          Token name (default: My Token).
  TOKEN_SYMBOL        Token symbol (default: MTK).
  TOKEN_DESCRIPTION   Description (default when unset: My Token Description; empty clears it).
  TOKEN_DISPLAY       Display denom (default: TOKEN_SYMBOL, or base denom when decimals is 0).
  TOKEN_DECIMALS      Decimals (default: 6; create-denom: 0-24, set-metadata: uint32).
  TOKEN_URI           Metadata URI (default: empty).
  TOKEN_URI_HASH      Metadata URI hash (default: empty).

Examples:
  $0 env
  CONFIRM_TX=yes $0 create-denom
  CONFIRM_TX=yes $0 set-metadata
  TOKEN_NAME='Research Token' TOKEN_SYMBOL=RSC TOKEN_DESCRIPTION='Updated description' CONFIRM_TX=yes $0 set-metadata
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

validate_token_decimals() {
  if [[ ! "$TOKEN_DECIMALS" =~ ^(0|[1-9][0-9]{0,9})$ ]] || [ "$TOKEN_DECIMALS" -gt 4294967295 ]; then
    echo "TOKEN_DECIMALS must be an integer from 0 to 4294967295 without leading zeros." >&2
    exit 1
  fi
  if [ "$ACTION" = "create-denom" ] && [ "$TOKEN_DECIMALS" -gt 24 ]; then
    echo "create-denom supports TOKEN_DECIMALS from 0 to 24." >&2
    exit 1
  fi
}

resolve_token_display() {
  if [ -z "$TOKEN_DISPLAY" ]; then
    if [ "$TOKEN_DECIMALS" = "0" ]; then
      TOKEN_DISPLAY="$DENOM"
    else
      TOKEN_DISPLAY="$TOKEN_SYMBOL"
    fi
  fi
  if [ "$TOKEN_DECIMALS" = "0" ] && [ "$TOKEN_DISPLAY" != "$DENOM" ]; then
    echo "TOKEN_DISPLAY must equal the base denom when TOKEN_DECIMALS is 0." >&2
    exit 1
  fi
}

case "$ACTION" in
  env)
    validate_token_decimals
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    resolve_token_display
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
    for METADATA_VAR in TOKEN_NAME TOKEN_SYMBOL TOKEN_DESCRIPTION TOKEN_DISPLAY TOKEN_DECIMALS TOKEN_URI TOKEN_URI_HASH; do
      printf 'export %s=%q\n' "$METADATA_VAR" "${!METADATA_VAR}"
    done
    ;;
  create-denom)
    require_confirm
    validate_token_decimals
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    injectived tx tokenfactory create-denom \
      "$SUBDENOM" \
      "$TOKEN_NAME" \
      "$TOKEN_SYMBOL" \
      "$TOKEN_DECIMALS" \
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
    validate_token_decimals
    CREATOR_ADDR="$(creator_addr)"
    DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
    resolve_token_display
    METADATA_HELP="$(injectived tx tokenfactory set-denom-metadata --help)"
    if grep -Fq '[shouldDisableAdminBurn]' <<< "$METADATA_HELP"; then
      METADATA_ARGS=("$TOKEN_DECIMALS" false)
    elif grep -Eq 'set-denom-metadata .*\[decimals\]([[:space:]]+\[flags\])?[[:space:]]*$' <<< "$METADATA_HELP"; then
      METADATA_ARGS=("$TOKEN_DECIMALS")
    else
      printf '%s\n' "$METADATA_HELP" >&2
      echo "Unsupported set-denom-metadata Usage. Check the positional arguments before setting metadata." >&2
      exit 1
    fi
    METADATA_DENOM_UNITS="$(jq -cn \
      --arg base "$DENOM" \
      --arg display "$TOKEN_DISPLAY" \
      --argjson decimals "$TOKEN_DECIMALS" \
      '[{denom: $base, exponent: 0, aliases: []}]
       + if $display == $base then []
         else [{denom: $display, exponent: $decimals, aliases: []}] end')"
    injectived tx tokenfactory set-denom-metadata \
      "$TOKEN_DESCRIPTION" \
      "$DENOM" \
      "$TOKEN_DISPLAY" \
      "$TOKEN_NAME" \
      "$TOKEN_SYMBOL" \
      "$TOKEN_URI" \
      "$TOKEN_URI_HASH" \
      "$METADATA_DENOM_UNITS" \
      "${METADATA_ARGS[@]}" \
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
