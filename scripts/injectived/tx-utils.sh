#!/usr/bin/env bash
# Source this file in Bash so transaction results stay in the current shell.
if [ -z "${BASH_VERSION:-}" ]; then
  echo "Load scripts/injectived/tx-utils.sh in Bash. Run bash first, then source this file." >&2
  return 1
fi

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  echo "Source scripts/injectived/tx-utils.sh before using run_tx or wait_tx." >&2
  exit 1
fi

_injective_tx_tools() {
  local tool
  for tool in jq injectived; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      printf 'Required command not found: %s\n' "$tool" >&2
      return 127
    fi
  done
}

_injective_tx_config() {
  if [[ ! "${TX_MAX_ATTEMPTS:-30}" =~ ^[1-9][0-9]*$ ]]; then
    echo "TX_MAX_ATTEMPTS must be a positive integer." >&2
    return 2
  fi
  if [[ ! "${TX_RETRY_DELAY:-2}" =~ ^[0-9]+$ ]]; then
    echo "TX_RETRY_DELAY must be a non-negative integer." >&2
    return 2
  fi
}

_injective_tx_body() {
  jq -ces '
    if length == 1 then .[0] else error("expected one transaction JSON object") end
    | if type == "object" then (.tx_response // .) else error("expected transaction object") end
    | if type == "object" then . else error("expected transaction response object") end
  '
}

_injective_tx_hash() {
  jq -er '.txhash | select(type == "string") | select(test("^[A-Fa-f0-9]{64}$"))'
}

_injective_tx_uint() {
  jq -er --arg field "$1" '
    .[$field]
    | if type == "number" then select(. >= 0 and . == floor) | tostring
      elif type == "string" then select(test("^[0-9]+$"))
      else empty end
  '
}

run_tx() {
  local response body hash code status hash_var=""
  unset TX_HASH TX_RESULT || return "$?"
  if [ "${1-}" = "--hash-var" ]; then
    if [ "$#" -lt 2 ]; then
      echo "--hash-var requires an operation hash variable name." >&2
      return 2
    fi
    hash_var="$2"
    if [[ ! "$hash_var" =~ ^[A-Z][A-Z0-9_]*_TX_HASH$ ]]; then
      echo "--hash-var must name an uppercase operation variable ending in _TX_HASH." >&2
      return 2
    fi
    shift 2
    unset "$hash_var" || return "$?"
  fi
  if [ "$#" -eq 0 ]; then
    echo "Usage: run_tx [--hash-var OPERATION_TX_HASH] <transaction command...>" >&2
    return 2
  fi
  _injective_tx_tools || return "$?"
  _injective_tx_config || return "$?"

  # Capture only this one send. Polling below never invokes the send command.
  if response="$("$@")"; then
    :
  else
    status=$?
    [ -z "$response" ] || printf '%s\n' "$response" >&2
    printf 'Transaction command failed (exit %s).\n' "$status" >&2
    return "$status"
  fi
  if body="$(_injective_tx_body <<< "$response")"; then :; else
    status=$?
    echo "Invalid transaction submission JSON." >&2
    return "$status"
  fi
  if hash="$(_injective_tx_hash <<< "$body")"; then :; else
    status=$?
    echo "Transaction submission is missing a valid txhash." >&2
    return "$status"
  fi
  export TX_HASH="$hash" || return "$?"
  printf 'Submitted transaction: TX_HASH=%s\n' "$TX_HASH" >&2
  if code="$(_injective_tx_uint code <<< "$body")"; then :; else
    status=$?
    echo "Transaction submission is missing a valid code." >&2
    return "$status"
  fi
  if [[ ! "$code" =~ ^0+$ ]]; then
    printf 'Transaction was rejected during submission (code %s, TX_HASH=%s).\n' "$code" "$TX_HASH" >&2
    printf '%s\n' "$response" >&2
    return 1
  fi
  if wait_tx "$TX_HASH"; then
    if [ -n "$hash_var" ]; then
      export "$hash_var=$TX_HASH" || return "$?"
    fi
  else
    return "$?"
  fi
}

wait_tx() {
  local hash="${1-}" response body result_hash code height status
  local attempt=1 max_attempts="${TX_MAX_ATTEMPTS:-30}" delay="${TX_RETRY_DELAY:-2}"
  local last_status=0
  unset TX_HASH TX_RESULT || return "$?"
  if [ "$#" -ne 1 ] || [[ ! "$hash" =~ ^[A-Fa-f0-9]{64}$ ]]; then
    echo "Usage: wait_tx <64-character hexadecimal transaction hash>" >&2
    return 2
  fi
  _injective_tx_tools || return "$?"
  _injective_tx_config || return "$?"
  export TX_HASH="$hash" || return "$?"

  while [ "$attempt" -le "$max_attempts" ]; do
    if response="$(injectived q tx "$hash" \
      --chain-id="${CHAIN_ID:-injective-888}" \
      --node="${NODE:-https://injective-testnet-rpc.publicnode.com:443}" \
      --output json)"; then
      last_status=0
      if body="$(_injective_tx_body <<< "$response")"; then :; else
        status=$?
        echo "Invalid transaction query JSON." >&2
        return "$status"
      fi
      if result_hash="$(_injective_tx_hash <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid txhash." >&2
        return "$status"
      fi
      if jq -e --arg expected "$hash" \
        'ascii_downcase == ($expected | ascii_downcase)' <<< "\"$result_hash\"" >/dev/null; then :; else
        status=$?
        echo "Transaction query returned a different txhash." >&2
        return "$status"
      fi
      if code="$(_injective_tx_uint code <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid code." >&2
        return "$status"
      fi
      if height="$(_injective_tx_uint height <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid height." >&2
        return "$status"
      fi
      if [[ ! "$code" =~ ^0+$ ]]; then
        printf 'Transaction failed on chain (code %s, TX_HASH=%s).\n' "$code" "$TX_HASH" >&2
        printf '%s\n' "$response" >&2
        return 1
      fi
      if [[ ! "$height" =~ ^0+$ ]]; then
        export TX_RESULT="$response" || return "$?"
        printf '%s\n' "$TX_RESULT"
        return 0
      fi
    else
      last_status=$?
    fi
    if [ "$attempt" -lt "$max_attempts" ]; then
      sleep "$delay" || return "$?"
    fi
    attempt=$((attempt + 1))
  done
  printf 'Transaction confirmation timed out after %s attempts (TX_HASH=%s). Use wait_tx "$TX_HASH" to query again.\n' "$max_attempts" "$TX_HASH" >&2
  if [ "$last_status" -ne 0 ]; then
    return "$last_status"
  fi
  return 1
}

tx_event_value() {
  local event_type="${1-}" body keys status key
  if [ "$#" -lt 2 ] || [ -z "$event_type" ]; then
    echo "Usage: tx_event_value <event_type> <attribute_key> [alias_key...]" >&2
    return 2
  fi
  shift
  for key in "$@"; do
    if [ -z "$key" ]; then
      echo "Transaction event attribute keys must not be empty." >&2
      return 2
    fi
  done
  if ! command -v jq >/dev/null 2>&1; then
    echo "Required command not found: jq" >&2
    return 127
  fi
  if [ -z "${TX_RESULT:-}" ]; then
    echo "TX_RESULT is empty. Confirm a transaction before reading its events." >&2
    return 1
  fi
  if body="$(_injective_tx_body <<< "$TX_RESULT")"; then :; else
    status=$?
    echo "Invalid TX_RESULT JSON." >&2
    return "$status"
  fi
  if keys="$(jq -cn --args '$ARGS.positional' "$@")"; then :; else return "$?"; fi
  jq -er --arg event_type "$event_type" --argjson keys "$keys" '
    def normalize_value:
      if type == "string" then
        . as $raw | (try fromjson catch $raw)
        | if type == "string" then . else $raw end
      elif type == "number" then tostring
      else error("invalid event attribute value") end
      | select(length > 0);
    [(.events // [])[], ((.logs // [])[] | (.events // [])[])]
    | [ .[] | select(.type == $event_type) | (.attributes // [])[]
        | . as $attribute
        | if ($keys | index($attribute.key)) != null then .value
          elif ($keys | map(@base64) | index($attribute.key)) != null then
            .value | @base64d
          else empty end
        | normalize_value ]
    | unique
    | if length == 1 then .[0]
      else error("transaction event attribute is missing or ambiguous") end
  ' <<< "$body"
}
