#!/usr/bin/env bash
set -euo pipefail

SIMBLOCK_DIR="${SIMBLOCK_DIR:-$HOME/jikken/simblock}"
OUTPUT_DIR="${1:-$SIMBLOCK_DIR/simulator/src/dist/output}"
BLOCK_LIST="$OUTPUT_DIR/blockList.txt"

BLOCK_SIZE="${BLOCK_SIZE:-1000000}"
AVG_TX_SIZE="${AVG_TX_SIZE:-250}"
INTERVAL_SEC="${INTERVAL_SEC:-10}"

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
  exit 1
fi

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
echo "========================================"
