#!/usr/bin/env bash
set -euo pipefail

KEY_NAME="${KEY_NAME:-testwallet}"
KEYRING_BACKEND="${KEYRING_BACKEND:-test}"
OUTPUT_FILE="${OUTPUT_FILE:-instantiate_msg.json}"
TOKEN_NAME="${TOKEN_NAME:-My Token}"
TOKEN_SYMBOL="${TOKEN_SYMBOL:-MTK}"
TOKEN_DECIMALS="${TOKEN_DECIMALS:-6}"
INITIAL_BALANCE="${INITIAL_BALANCE:-1000000}"

if ! echo "$TOKEN_SYMBOL" | grep -Eq '^[A-Za-z-]{3,12}$'; then
  echo "Invalid TOKEN_SYMBOL: $TOKEN_SYMBOL" >&2
  echo "Use only letters or hyphen, 3 to 12 characters." >&2
  exit 1
fi

if [ -z "${CREATOR_ADDR:-}" ]; then
  if ! command -v injectived >/dev/null 2>&1; then
    echo "injectived command is required when CREATOR_ADDR is not set." >&2
    exit 1
  fi
  CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
fi

cat > "$OUTPUT_FILE" <<EOF
{
  "name": "$TOKEN_NAME",
  "symbol": "$TOKEN_SYMBOL",
  "decimals": $TOKEN_DECIMALS,
  "initial_balances": [
    {
      "address": "$CREATOR_ADDR",
      "amount": "$INITIAL_BALANCE"
    }
  ],
  "mint": {
    "minter": "$CREATOR_ADDR"
  },
  "marketing": null
}
EOF

jq . "$OUTPUT_FILE"
