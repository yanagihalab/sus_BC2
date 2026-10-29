#!/usr/bin/env bash
set -euo pipefail

# 集計方法は課題5・6で使う伝播集計スクリプトに統一する。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/calc_simblock_propagation.sh" "$@"
