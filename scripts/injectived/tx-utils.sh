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
  for tool in jq injectived mkdir mktemp chmod cat; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      printf 'Required command not found: %s\n' "$tool" >&2
      return 127
    fi
  done
}

_injective_tx_log_start() {
  local root directory status
  if [ -n "${TX_LOG_ROOT:-}" ]; then
    root="$TX_LOG_ROOT"
  elif [ -n "${XDG_STATE_HOME:-}" ]; then
    root="$XDG_STATE_HOME/sus_BC2/transactions"
  elif [ -n "${HOME:-}" ]; then
    root="$HOME/.local/state/sus_BC2/transactions"
  else
    echo "Set HOME, XDG_STATE_HOME, or TX_LOG_ROOT before recording transaction responses." >&2
    return 2
  fi
  case "$root" in /*) ;; *) root="$PWD/$root" ;; esac
  if directory="$(
    umask 077
    mkdir -p "$root" &&
    root="$(cd "$root" && pwd -P)" &&
    mktemp -d "$root/transaction.XXXXXXXXXX"
  )"; then :; else
    status=$?
    echo "Cannot create response log directory. No transaction command was executed." >&2
    return "$status"
  fi
  if chmod 700 "$directory"; then :; else
    status=$?
    echo "Cannot secure response log directory. No transaction command was executed." >&2
    return "$status"
  fi
  export TX_LOG_DIR="$directory" || return "$?"
  printf 'Transaction response logs: TX_LOG_DIR=%s\n' "$TX_LOG_DIR" >&2
}

# Run in a subshell, preserving the caller's umask and isolating command functions.
# On success stdout contains only the CLI status; a nonzero return is a log failure.
_injective_tx_capture() (
  local directory="$1" prefix="$2" status log_status extension command_umask
  shift 2
  command_umask="$(umask)"
  umask 077
  for extension in stdout stderr status; do
    if : > "$directory/$prefix.$extension"; then :; else
      status=$?
      echo "Cannot prepare response log files. No command was executed." >&2
      return "$status"
    fi
  done
  if chmod 600 "$directory/$prefix.stdout" "$directory/$prefix.stderr" "$directory/$prefix.status"; then :; else
    status=$?
    echo "Cannot secure response log files. No command was executed." >&2
    return "$status"
  fi
  if (umask "$command_umask" && "$@") > "$directory/$prefix.stdout" 2> "$directory/$prefix.stderr"; then
    status=0
  else
    status=$?
  fi
  if printf '%s\n' "$status" > "$directory/$prefix.status"; then
    log_status=0
  else
    log_status=$?
    echo "Cannot record the command exit status. The transaction state may be unknown." >&2
  fi
  if cat "$directory/$prefix.stderr" >&2; then :; else
    echo "Cannot replay command stderr; inspect its response log directly." >&2
  fi
  if [ "$log_status" -ne 0 ]; then
    if [ "$status" -ne 0 ]; then return "$status"; fi
    return "$log_status"
  fi
  printf '%s\n' "$status"
)

_injective_tx_log_notice() {
  printf 'Transaction state may be unknown. Inspect response logs in %s. Do not resend; confirm the transaction state first.\n' "$TX_LOG_DIR" >&2
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
  local response body hash code status command_status hash_var=""
  unset TX_HASH TX_RESULT TX_LOG_DIR || return "$?"
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
  _injective_tx_log_start || return "$?"

  # Save the one send response verbatim before reading or parsing any of it.
  if command_status="$(_injective_tx_capture "$TX_LOG_DIR" submission "$@")"; then :; else
    status=$?
    _injective_tx_log_notice
    return "$status"
  fi
  if [ "$command_status" -ne 0 ]; then
    if cat "$TX_LOG_DIR/submission.stdout" >&2; then :; else
      echo "Cannot replay command stdout; inspect its response log directly." >&2
    fi
    printf 'Transaction command failed (exit %s); submission may already have occurred.\n' "$command_status" >&2
    _injective_tx_log_notice
    return "$command_status"
  fi
  if body="$(_injective_tx_body < "$TX_LOG_DIR/submission.stdout")"; then :; else
    status=$?
    echo "Invalid transaction submission JSON." >&2
    _injective_tx_log_notice
    return "$status"
  fi
  if response="$(cat "$TX_LOG_DIR/submission.stdout")"; then :; else
    status=$?
    echo "Cannot read the recorded transaction submission response." >&2
    _injective_tx_log_notice
    return "$status"
  fi
  if hash="$(_injective_tx_hash <<< "$body")"; then :; else
    status=$?
    echo "Transaction submission is missing a valid txhash." >&2
    _injective_tx_log_notice
    return "$status"
  fi
  export TX_HASH="$hash" || return "$?"
  printf 'Submitted transaction: TX_HASH=%s\n' "$TX_HASH" >&2
  if code="$(_injective_tx_uint code <<< "$body")"; then :; else
    status=$?
    echo "Transaction submission is missing a valid code." >&2
    _injective_tx_log_notice
    return "$status"
  fi
  if [[ ! "$code" =~ ^0+$ ]]; then
    printf 'Transaction was rejected during submission (code %s, TX_HASH=%s).\n' "$code" "$TX_HASH" >&2
    printf '%s\n' "$response" >&2
    _injective_tx_log_notice
    return 1
  fi
  if _injective_tx_wait "$TX_HASH"; then
    if [ -n "$hash_var" ]; then
      export "$hash_var=$TX_HASH" || return "$?"
    fi
  else
    return "$?"
  fi
}

wait_tx() {
  local hash="${1-}"
  unset TX_HASH TX_RESULT TX_LOG_DIR || return "$?"
  if [ "$#" -ne 1 ] || [[ ! "$hash" =~ ^[A-Fa-f0-9]{64}$ ]]; then
    echo "Usage: wait_tx <64-character hexadecimal transaction hash>" >&2
    return 2
  fi
  _injective_tx_tools || return "$?"
  _injective_tx_config || return "$?"
  _injective_tx_log_start || return "$?"
  export TX_HASH="$hash" || return "$?"
  _injective_tx_wait "$hash"
}

_injective_tx_wait() {
  local hash="$1" response body result_hash code height status command_status
  local attempt=1 max_attempts="${TX_MAX_ATTEMPTS:-30}" delay="${TX_RETRY_DELAY:-2}"
  local last_status=0
  while [ "$attempt" -le "$max_attempts" ]; do
    if command_status="$(_injective_tx_capture "$TX_LOG_DIR" "query-$attempt" injectived q tx "$hash" \
      --chain-id="${CHAIN_ID:-injective-888}" \
      --node="${NODE:-https://injective-testnet-rpc.publicnode.com:443}" \
      --output json)"; then :; else
      status=$?
      _injective_tx_log_notice
      return "$status"
    fi
    if [ "$command_status" -eq 0 ]; then
      last_status=0
      if body="$(_injective_tx_body < "$TX_LOG_DIR/query-$attempt.stdout")"; then :; else
        status=$?
        echo "Invalid transaction query JSON." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if response="$(cat "$TX_LOG_DIR/query-$attempt.stdout")"; then :; else
        status=$?
        echo "Cannot read the recorded transaction query response." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if result_hash="$(_injective_tx_hash <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid txhash." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if jq -e --arg expected "$hash" \
        'ascii_downcase == ($expected | ascii_downcase)' <<< "\"$result_hash\"" >/dev/null; then :; else
        status=$?
        echo "Transaction query returned a different txhash." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if code="$(_injective_tx_uint code <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid code." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if height="$(_injective_tx_uint height <<< "$body")"; then :; else
        status=$?
        echo "Transaction query is missing a valid height." >&2
        _injective_tx_log_notice
        return "$status"
      fi
      if [[ ! "$code" =~ ^0+$ ]]; then
        printf 'Transaction failed on chain (code %s, TX_HASH=%s).\n' "$code" "$TX_HASH" >&2
        printf '%s\n' "$response" >&2
        _injective_tx_log_notice
        return 1
      fi
      if [[ ! "$height" =~ ^0+$ ]]; then
        export TX_RESULT="$response" || return "$?"
        printf '%s\n' "$TX_RESULT"
        return 0
      fi
    else
      last_status="$command_status"
    fi
    if [ "$attempt" -lt "$max_attempts" ]; then
      sleep "$delay" || return "$?"
    fi
    attempt=$((attempt + 1))
  done
  printf 'Transaction confirmation timed out after %s attempts (TX_HASH=%s). Use wait_tx "$TX_HASH" to query again.\n' "$max_attempts" "$TX_HASH" >&2
  _injective_tx_log_notice
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
