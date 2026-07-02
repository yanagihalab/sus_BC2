#!/usr/bin/env bash
set -euo pipefail

SIMBLOCK_DIR="${SIMBLOCK_DIR:-$HOME/jikken/simblock}"
OUTPUT_DIR="${1:-$SIMBLOCK_DIR/simulator/src/dist/output}"
BLOCK_LIST="$OUTPUT_DIR/blockList.txt"
OUTPUT_JSON="${OUTPUT_JSON:-$OUTPUT_DIR/output.json}"
PROPAGATION_FILE="${PROPAGATION_FILE:-}"

BLOCK_SIZE="${BLOCK_SIZE:-1000000}"
AVG_TX_SIZE="${AVG_TX_SIZE:-250}"
INTERVAL_SEC="${INTERVAL_SEC:-10}"

find_propagation_file() {
  if [ -n "$PROPAGATION_FILE" ]; then
    return
  fi

  for candidate in \
    "$OUTPUT_DIR/propagation.txt" \
    "$OUTPUT_DIR/propagation.log" \
    "$OUTPUT_DIR/out.txt" \
    "$OUTPUT_DIR/stdout.txt" \
    "$OUTPUT_DIR/simblock_stdout.txt"; do
    if [ -f "$candidate" ]; then
      PROPAGATION_FILE="$candidate"
      return
    fi
  done
}

if [ ! -f "$BLOCK_LIST" ]; then
  echo "[ERROR] blockList.txt not found: $BLOCK_LIST"
  echo ""
  echo "Usage:"
  echo "  ./calc_simblock_metrics.sh [output_dir]"
  echo ""
  echo "Example:"
  echo "  ./calc_simblock_metrics.sh ~/jikken/simblock/simulator/src/dist/output"
  echo ""
  echo "Optional environment variables:"
  echo "  BLOCK_SIZE=1000000"
  echo "  AVG_TX_SIZE=250"
  echo "  INTERVAL_SEC=10"
  echo "  SIMBLOCK_DIR=$HOME/jikken/simblock"
  echo "  OUTPUT_JSON=/path/to/output.json"
  echo "  PROPAGATION_FILE=/path/to/propagation.txt"
  exit 1
fi

find_propagation_file

ONCHAIN=$(grep -c "OnChain" "$BLOCK_LIST" || true)
ORPHAN=$(grep -c "Orphan" "$BLOCK_LIST" || true)
ALL=$(wc -l < "$BLOCK_LIST" | tr -d ' ')

if [ "$ALL" -eq 0 ]; then
  echo "[ERROR] blockList.txt is empty: $BLOCK_LIST"
  exit 1
fi

if [ "$AVG_TX_SIZE" -le 0 ]; then
  echo "[ERROR] AVG_TX_SIZE must be greater than 0"
  exit 1
fi

if [ "$INTERVAL_SEC" -le 0 ]; then
  echo "[ERROR] INTERVAL_SEC must be greater than 0"
  exit 1
fi

TX_PER_BLOCK=$((BLOCK_SIZE / AVG_TX_SIZE))
SIM_TIME_SEC=$((ONCHAIN * INTERVAL_SEC))

FORK_EVENTS_BY_HEIGHT=$(awk -F ':' '
  function trim(s) {
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
    return s
  }
  NF >= 2 {
    height = trim($2)
    if (height != "") {
      block_count[height]++
    }
  }
  END {
    forks = 0
    max_competing = 0
    for (height in block_count) {
      if (block_count[height] > 1) {
        forks++
      }
      if (block_count[height] > max_competing) {
        max_competing = block_count[height]
      }
    }
    printf("%d", forks)
  }
' "$BLOCK_LIST")

ORPHAN_HEIGHTS=$(awk -F ':' '
  function trim(s) {
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
    return s
  }
  $1 ~ /Orphan/ && NF >= 2 {
    height = trim($2)
    if (height != "") {
      orphan_height[height] = 1
    }
  }
  END {
    count = 0
    for (height in orphan_height) {
      count++
    }
    printf("%d", count)
  }
' "$BLOCK_LIST")

MAX_COMPETING_BLOCKS_AT_HEIGHT=$(awk -F ':' '
  function trim(s) {
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
    return s
  }
  NF >= 2 {
    height = trim($2)
    if (height != "") {
      block_count[height]++
    }
  }
  END {
    max_competing = 0
    for (height in block_count) {
      if (block_count[height] > max_competing) {
        max_competing = block_count[height]
      }
    }
    printf("%d", max_competing)
  }
' "$BLOCK_LIST")

FORK_RATE=$(awk -v o="$ORPHAN" -v a="$ALL" 'BEGIN { printf("%.6f", o / a) }')
FORK_RATE_PERCENT=$(awk -v o="$ORPHAN" -v a="$ALL" 'BEGIN { printf("%.2f", (o / a) * 100) }')

EFFECTIVE_TPS=$(awk -v b="$ONCHAIN" -v tx="$TX_PER_BLOCK" -v t="$SIM_TIME_SEC" \
  'BEGIN {
    if (t == 0) {
      printf("0.00")
    } else {
      printf("%.2f", (b * tx) / t)
    }
  }')

TPS_FROM_INTERVAL=$(awk -v tx="$TX_PER_BLOCK" -v sec="$INTERVAL_SEC" \
  'BEGIN { printf("%.2f", tx / sec) }')

GENERATED_BLOCK_TPS=$(awk -v b="$ALL" -v tx="$TX_PER_BLOCK" -v t="$SIM_TIME_SEC" \
  'BEGIN {
    if (t == 0) {
      printf("0.00")
    } else {
      printf("%.2f", (b * tx) / t)
    }
  }')

PROPAGATION_STATUS="not_found"
PROPAGATION_BLOCKS="N/A"
PROPAGATION_NODE_ARRIVALS="N/A"
AVG_BLOCK_PROPAGATION_MS="N/A"
AVG_NODE_ARRIVAL_MS="N/A"
MAX_NODE_ARRIVAL_MS="N/A"

if [ -n "$PROPAGATION_FILE" ] && [ -f "$PROPAGATION_FILE" ]; then
  PROPAGATION_STATUS="ok"
  while IFS='=' read -r key value; do
    case "$key" in
      propagation_blocks) PROPAGATION_BLOCKS="$value" ;;
      node_arrivals) PROPAGATION_NODE_ARRIVALS="$value" ;;
      avg_block_propagation_ms) AVG_BLOCK_PROPAGATION_MS="$value" ;;
      avg_node_arrival_ms) AVG_NODE_ARRIVAL_MS="$value" ;;
      max_node_arrival_ms) MAX_NODE_ARRIVAL_MS="$value" ;;
    esac
  done < <(awk '
    function emit_results() {
      block_total = 0
      block_sum = 0
      for (block in block_seen) {
        if (block_sample_count[block] > 0) {
          block_total++
          block_sum += block_max[block]
        }
      }
      if (sample_count == 0 || block_total == 0) {
        print "propagation_blocks=0"
        print "node_arrivals=0"
        print "avg_block_propagation_ms=N/A"
        print "avg_node_arrival_ms=N/A"
        print "max_node_arrival_ms=N/A"
      } else {
        printf("propagation_blocks=%d\n", block_total)
        printf("node_arrivals=%d\n", sample_count)
        printf("avg_block_propagation_ms=%.2f\n", block_sum / block_total)
        printf("avg_node_arrival_ms=%.2f\n", sample_sum / sample_count)
        printf("max_node_arrival_ms=%.2f\n", max_sample)
      }
    }
    /^[[:space:]]*$/ {
      current_block = ""
      next
    }
    /^[[:space:]]*[0-9]+[[:space:]]*,[[:space:]]*[0-9]+([.][0-9]+)?[[:space:]]*$/ {
      if (current_block == "") {
        next
      }
      line = $0
      gsub(/[[:space:]]/, "", line)
      split(line, fields, ",")
      arrival = fields[2] + 0
      block_seen[current_block] = 1
      block_sample_count[current_block]++
      if (arrival > block_max[current_block]) {
        block_max[current_block] = arrival
      }
      sample_count++
      sample_sum += arrival
      if (arrival > max_sample) {
        max_sample = arrival
      }
      next
    }
    {
      current_block = $0
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", current_block)
      if (current_block != "") {
        block_seen[current_block] = 1
      }
    }
    END {
      emit_results()
    }
  ' "$PROPAGATION_FILE")
fi

FLOW_STATUS="not_found"
FLOW_BLOCK_MESSAGES="N/A"
FLOW_BLOCKS="N/A"
AVG_MESSAGE_DELAY_MS="N/A"
AVG_FLOW_BLOCK_PROPAGATION_MS="N/A"
AVG_FLOW_NODE_ARRIVAL_MS="N/A"
MAX_FLOW_NODE_ARRIVAL_MS="N/A"

if [ -f "$OUTPUT_JSON" ]; then
  if command -v jq >/dev/null 2>&1; then
    FLOW_STATUS="ok"
    while IFS='=' read -r key value; do
      case "$key" in
        flow_block_messages) FLOW_BLOCK_MESSAGES="$value" ;;
        flow_blocks) FLOW_BLOCKS="$value" ;;
        avg_message_delay_ms) AVG_MESSAGE_DELAY_MS="$value" ;;
        avg_flow_block_propagation_ms) AVG_FLOW_BLOCK_PROPAGATION_MS="$value" ;;
        avg_flow_node_arrival_ms) AVG_FLOW_NODE_ARRIVAL_MS="$value" ;;
        max_flow_node_arrival_ms) MAX_FLOW_NODE_ARRIVAL_MS="$value" ;;
      esac
    done < <(jq -r '
      .[]
      | select(.kind == "flow-block")
      | .content
      | [
          ."block-id",
          ."begin-node-id",
          ."end-node-id",
          ."transmission-timestamp",
          ."reception-timestamp"
        ]
      | @tsv
    ' "$OUTPUT_JSON" | awk '
      NF >= 5 {
        block = $1
        end_node = $3
        tx = $4 + 0
        rx = $5 + 0
        delay = rx - tx

        message_count++
        delay_sum += delay

        if (!(block in first_tx) || tx < first_tx[block]) {
          first_tx[block] = tx
        }
        blocks[block] = 1

        arrival_key = block SUBSEP end_node
        if (!(arrival_key in first_rx) || rx < first_rx[arrival_key]) {
          first_rx[arrival_key] = rx
        }
      }
      END {
        if (message_count == 0) {
          print "flow_block_messages=0"
          print "flow_blocks=0"
          print "avg_message_delay_ms=N/A"
          print "avg_flow_block_propagation_ms=N/A"
          print "avg_flow_node_arrival_ms=N/A"
          print "max_flow_node_arrival_ms=N/A"
          exit
        }

        for (arrival_key in first_rx) {
          split(arrival_key, parts, SUBSEP)
          block = parts[1]
          arrival = first_rx[arrival_key] - first_tx[block]
          arrival_count++
          arrival_sum += arrival
          if (arrival > block_max_arrival[block]) {
            block_max_arrival[block] = arrival
          }
          if (arrival > max_arrival) {
            max_arrival = arrival
          }
        }

        block_count = 0
        block_sum = 0
        for (block in blocks) {
          block_count++
          block_sum += block_max_arrival[block]
        }

        printf("flow_block_messages=%d\n", message_count)
        printf("flow_blocks=%d\n", block_count)
        printf("avg_message_delay_ms=%.2f\n", delay_sum / message_count)
        printf("avg_flow_block_propagation_ms=%.2f\n", block_sum / block_count)
        printf("avg_flow_node_arrival_ms=%.2f\n", arrival_sum / arrival_count)
        printf("max_flow_node_arrival_ms=%.2f\n", max_arrival)
      }
    ')
  else
    FLOW_STATUS="jq_not_found"
  fi
fi

echo "========================================"
echo "SimBlock Metrics"
echo "========================================"
echo "output_dir              : $OUTPUT_DIR"
echo "block_list              : $BLOCK_LIST"
echo ""
echo "[Block counts]"
echo "onchain_blocks          : $ONCHAIN"
echo "orphan_blocks           : $ORPHAN"
echo "all_generated_blocks    : $ALL"
echo ""
echo "[Fork / orphan rate]"
echo "fork_rate               : $FORK_RATE"
echo "fork_rate_percent       : ${FORK_RATE_PERCENT}%"
echo "orphan_rate             : $FORK_RATE"
echo "orphan_rate_percent     : ${FORK_RATE_PERCENT}%"
echo ""
echo "[Fork events]"
echo "fork_events_by_height   : $FORK_EVENTS_BY_HEIGHT"
echo "orphan_heights          : $ORPHAN_HEIGHTS"
echo "max_blocks_same_height  : $MAX_COMPETING_BLOCKS_AT_HEIGHT"
echo ""
echo "[Propagation metrics]"
echo "propagation_file        : ${PROPAGATION_FILE:-N/A}"
echo "propagation_status      : $PROPAGATION_STATUS"
echo "propagation_blocks      : $PROPAGATION_BLOCKS"
echo "node_arrivals           : $PROPAGATION_NODE_ARRIVALS"
echo "avg_block_propagation_ms: $AVG_BLOCK_PROPAGATION_MS"
echo "avg_node_arrival_ms     : $AVG_NODE_ARRIVAL_MS"
echo "max_node_arrival_ms     : $MAX_NODE_ARRIVAL_MS"
echo ""
echo "[Output JSON flow metrics]"
echo "output_json             : $OUTPUT_JSON"
echo "flow_status             : $FLOW_STATUS"
echo "flow_block_messages     : $FLOW_BLOCK_MESSAGES"
echo "flow_blocks             : $FLOW_BLOCKS"
echo "avg_message_delay_ms    : $AVG_MESSAGE_DELAY_MS"
echo "avg_flow_block_propagation_ms: $AVG_FLOW_BLOCK_PROPAGATION_MS"
echo "avg_flow_node_arrival_ms: $AVG_FLOW_NODE_ARRIVAL_MS"
echo "max_flow_node_arrival_ms: $MAX_FLOW_NODE_ARRIVAL_MS"
echo ""
echo "[TPS estimation settings]"
echo "block_size_bytes        : $BLOCK_SIZE"
echo "avg_tx_size_bytes       : $AVG_TX_SIZE"
echo "tx_per_block            : $TX_PER_BLOCK"
echo "interval_sec            : $INTERVAL_SEC"
echo "estimated_sim_time_sec  : $SIM_TIME_SEC"
echo ""
echo "[TPS]"
echo "effective_tps_onchain   : $EFFECTIVE_TPS"
echo "tps_from_interval       : $TPS_FROM_INTERVAL"
echo "generated_block_tps     : $GENERATED_BLOCK_TPS"
echo ""
echo "Notes:"
echo "  effective_tps_onchain uses only OnChain blocks."
echo "  generated_block_tps includes Orphan blocks and is not final-chain TPS."
echo "  fork_events_by_height counts block heights where multiple blocks were generated."
echo "  propagation metrics use SimBlock propagation stdout captured to PROPAGATION_FILE."
echo "  output JSON flow metrics use flow-block events from output.json."
echo "========================================"
