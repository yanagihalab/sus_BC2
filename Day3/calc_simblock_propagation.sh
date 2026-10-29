#!/usr/bin/env bash
set -euo pipefail

# Java の INTERVAL はミリ秒。集計用 INTERVAL_SEC は秒（600000 ms = 600 s）。
python3 - "$@" <<'PY'
import csv
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
from collections import Counter, defaultdict


def positive_integer(name, default):
    value = os.environ.get(name, str(default))
    if not re.fullmatch(r"[0-9]+", value) or int(value) <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def percentile(values, percent):
    ordered = sorted(values)
    return ordered[math.ceil(percent / 100 * len(ordered)) - 1]


def unavailable(error, num_nodes=0):
    return {
        "propagation_available": 0, "propagation_error": error,
        "propagation_time_unit": "milliseconds", "num_nodes": num_nodes,
        "parsed_blocks": 0, "fully_reached_blocks": 0, "partially_reached_blocks": 0,
        "full_reach_propagation_available": 0,
        "full_reach_average_block_propagation_time": "N/A",
        "full_reach_average_90pct_node_arrival_time": "N/A",
        "full_reach_average_95pct_node_arrival_time": "N/A",
    }


def propagation_metrics(output_dir):
    csv_path = output_dir / "propagation_metrics_from_add_block.csv"
    # 前回の CSV を今回の集計結果として使わない。
    csv_path.unlink(missing_ok=True)
    output_json = output_dir / "output.json"
    if not output_json.is_file():
        return unavailable("output_json_not_found")
    events = json.loads(output_json.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError("output.json must contain a list of events")

    node_ids = set()
    arrivals = defaultdict(dict)
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("content"), dict):
            continue
        content = event["content"]
        if event.get("kind") == "add-node" and content.get("node-id") is not None:
            node_ids.add(int(content["node-id"]))
        elif event.get("kind") == "add-block":
            if any(content.get(key) is None for key in ("block-id", "node-id", "timestamp")):
                continue
            block, node = int(content["block-id"]), int(content["node-id"])
            timestamp = float(content["timestamp"])
            if not math.isfinite(timestamp):
                raise ValueError("add-block timestamp must be finite")
            arrivals[block][node] = min(arrivals[block].get(node, timestamp), timestamp)

    if not node_ids:
        return unavailable("no_add_node_data")

    rows, complete_rows = [], []
    for block, node_times in sorted(arrivals.items()):
        if not set(node_times).issubset(node_ids):
            raise ValueError("add-block refers to a node missing from add-node events")
        if len(node_times) < 2:
            continue
        generation = min(node_times.values())
        times = [timestamp - generation for timestamp in node_times.values()]
        complete = set(node_times) == node_ids
        # 未到達を丸めて 100% と表示しない。完全到達の判定はノード集合で行う。
        rate = 100.0 if complete else min(len(times) / len(node_ids) * 100, 99.999999)
        row = {
            "block_id": block, "generation_time": generation,
            "reached_nodes": len(times), "reached_rate": rate,
            "avg_time": statistics.mean(times), "p90_time": percentile(times, 90),
            "p95_time": percentile(times, 95), "max_time": max(times),
        }
        rows.append(row)
        if complete:
            complete_rows.append(row)

    if not rows:
        return unavailable("no_add_block_data", len(node_ids))

    columns = ["block_id", "generation_time", "reached_nodes", "reached_rate",
               "avg_time", "p90_time", "p95_time", "max_time"]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.6f}" if isinstance(value, float) else value
                             for key, value in row.items()})

    result = {
        "propagation_available": 1, "propagation_time_unit": "milliseconds",
        "num_nodes": len(node_ids), "parsed_blocks": len(rows),
        "fully_reached_blocks": len(complete_rows),
        "partially_reached_blocks": len(rows) - len(complete_rows),
        "full_reach_propagation_available": int(bool(complete_rows)),
        "propagation_csv": csv_path,
    }
    # まず各ブロック内で計算し、その値をブロック間で平均する。
    for field, label in (("avg_time", "block_propagation_time"),
                         ("p90_time", "90pct_node_arrival_time"),
                         ("p95_time", "95pct_node_arrival_time"),
                         ("max_time", "max_node_arrival_time")):
        result[f"average_{label}"] = f"{statistics.mean(row[field] for row in rows):.6f}"
        if field != "max_time":
            result[f"full_reach_average_{label}"] = (
                f"{statistics.mean(row[field] for row in complete_rows):.6f}"
                if complete_rows else "N/A"
            )
    return result


def main():
    if sys.argv[1:] in (["--help"], ["-h"]):
        print("Usage: bash calc_simblock_propagation.sh [output_dir]")
        print("Settings: BLOCK_SIZE=1000000 AVG_TX_SIZE=250 INTERVAL_SEC=600")
        print("BLOCK_SIZE/AVG_TX_SIZE: bytes; INTERVAL_SEC: seconds; propagation: milliseconds")
        return 0
    if len(sys.argv) > 2:
        raise ValueError("Usage: bash calc_simblock_propagation.sh [output_dir]")

    simblock = Path(os.environ.get("SIMBLOCK_DIR", str(Path.home() / "jikken/simblock")))
    output_dir = Path(sys.argv[1]) if len(sys.argv) == 2 else simblock / "simulator/src/dist/output"
    block_list = output_dir / "blockList.txt"
    block_size = positive_integer("BLOCK_SIZE", 1000000)
    tx_size = positive_integer("AVG_TX_SIZE", 250)
    interval = positive_integer("INTERVAL_SEC", 600)

    # 標準の status 行だけを数え、空行や末尾改行の有無を分母へ含めない。
    states = Counter()
    for line in block_list.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(OnChain|Orphan)\s*:", line)
        if match:
            states[match[1]] += 1
    onchain, orphan = states["OnChain"], states["Orphan"]
    total = onchain + orphan
    if total == 0:
        raise ValueError(f"blockList.txt is empty or has no OnChain/Orphan records: {block_list}")
    tx_per_block = block_size // tx_size
    sim_time = onchain * interval

    print("SimBlock Metrics")
    print(f"output_dir : {output_dir}")
    print(f"block_list : {block_list}")
    print(f"output_json : {output_dir / 'output.json'}")
    print(f"onchain_blocks : {onchain}")
    print(f"orphan_blocks : {orphan}")
    print(f"all_generated_blocks : {total}")
    print(f"fork_count : {orphan}")
    print(f"fork_rate : {orphan / total:.6f}")
    print(f"fork_rate_percent : {orphan / total * 100:.2f}%")
    print(f"orphan_rate : {orphan / total:.6f}")
    print(f"orphan_rate_percent : {orphan / total * 100:.2f}%")
    print(f"block_size_bytes : {block_size}")
    print(f"avg_tx_size_bytes : {tx_size}")
    print(f"tx_per_block : {tx_per_block}")
    print(f"interval_sec : {interval}")
    print(f"estimated_sim_time_sec : {sim_time}")
    print(f"effective_tps_onchain : {onchain * tx_per_block / sim_time if sim_time else 0:.2f}")
    print(f"tps_from_interval : {tx_per_block / interval:.2f}")
    print(f"generated_block_tps : {total * tx_per_block / sim_time if sim_time else 0:.2f}")
    for key, value in propagation_metrics(output_dir).items():
        print(f"{key} : {value}")
    return 0


try:
    raise SystemExit(main())
except (OSError, ValueError, TypeError, KeyError) as error:
    print(f"[ERROR] {error}", file=sys.stderr)
    raise SystemExit(1)
PY
