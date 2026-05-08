#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

INPUT_DIR = Path("./*__*")
OUTPUT_DIR = Path("./Proposer-visualizer/out")
OUTPUT_CSV = "proposer_sequence.csv"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def collect_input_files(input_dir: Path) -> List[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    return sorted(p for p in input_dir.iterdir() if p.suffix.lower() == ".json")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["_source_file"] = path.name
    return data


def block_sort_key(data: Dict[str, Any]) -> Tuple[int, str]:
    height_str = safe_get(data, "blockheader", "height", default="0")
    time_str = safe_get(data, "blockheader", "time", default="")
    try:
        height = int(height_str)
    except (TypeError, ValueError):
        height = -1
    return (height, time_str)


def short_hex(hex_str: str, left: int = 6, right: int = 4) -> str:
    s = str(hex_str).strip().upper()
    if len(s) <= left + right:
        return s
    return f"{s[:left]}…{s[-right:]}"


def proposer_moniker_from_block(data: Dict[str, Any], proposer_hex: str) -> str:
    validators = data.get("validators", []) or []
    for v in validators:
        if str(v.get("address", "")).upper() == proposer_hex.upper():
            return short_hex(proposer_hex)
    return short_hex(proposer_hex)


def build_sequence_rows(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for data in blocks:
        blockheader = data.get("blockheader", {})
        height = blockheader.get("height", "")
        time = blockheader.get("time", "")
        proposer_hex = str(blockheader.get("proposer_address", "")).upper().strip()

        if not height or not proposer_hex:
            continue

        proposer_moniker = proposer_moniker_from_block(data, proposer_hex)

        rows.append(
            {
                "height": height,
                "time": time,
                "proposer_hex": proposer_hex,
                "proposer_moniker": proposer_moniker,
            }
        )

    rows.sort(key=lambda r: int(r["height"]))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = ["height", "time", "proposer_hex", "proposer_moniker"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    input_files = collect_input_files(INPUT_DIR)
    if not input_files:
        raise RuntimeError(f"No JSON files found in {INPUT_DIR}")

    ensure_dir(OUTPUT_DIR)

    blocks = [load_json(p) for p in input_files]
    blocks.sort(key=block_sort_key)

    rows = build_sequence_rows(blocks)

    out_path = OUTPUT_DIR / OUTPUT_CSV
    write_csv(out_path, rows)

    print(f"[OK] input files : {len(input_files)}")
    print(f"[OK] input dir   : {INPUT_DIR}")
    print(f"[OK] output file : {out_path}")
    print(f"[OK] rows        : {len(rows)}")

    if rows:
        print("[OK] first row   :", rows[0])
        print("[OK] last row    :", rows[-1])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())