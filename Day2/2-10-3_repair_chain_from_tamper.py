#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import hashlib
import time
from pathlib import Path

INPUT_FILE = "blockchain_1000_tampered.json"
OUTPUT_FILE = "blockchain_1000_tampered_repaired_pow.json"

START_INDEX = 500

DIFFICULTY = 5
MAX_NONCE = 10_000_000


def calculate_hash(block):
    block_for_hash = {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "data": block["data"],
        "previous_hash": block["previous_hash"],
        "nonce": block["nonce"]
    }

    block_string = json.dumps(
        block_for_hash,
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


def mine_block(block, difficulty, max_nonce):
    prefix = "0" * difficulty

    start_time = time.perf_counter()

    for nonce in range(max_nonce + 1):
        block["nonce"] = nonce
        block_hash = calculate_hash(block)

        if block_hash.startswith(prefix):
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            return block_hash, nonce, elapsed_time

    raise RuntimeError(
        "PoW failed: valid nonce was not found within max_nonce"
    )


def main():
    input_path = Path(INPUT_FILE)

    if not input_path.exists():
        print("エラー: 入力ファイルが見つかりません:", INPUT_FILE)
        return 1

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        blockchain = json.load(f)

    if START_INDEX < 0:
        print("エラー: START_INDEX は0以上にしてください。")
        return 1

    if START_INDEX >= len(blockchain):
        print("エラー: START_INDEX がブロック数以上です。")
        return 1

    if DIFFICULTY < 1:
        print("エラー: DIFFICULTY は1以上にしてください。")
        return 1

    print("=== PoW chain repair started ===")
    print("input file  :", INPUT_FILE)
    print("output file :", OUTPUT_FILE)
    print("start index :", START_INDEX)
    print("difficulty  :", DIFFICULTY)
    print("max_nonce   :", MAX_NONCE)
    print()

    total_start_time = time.perf_counter()

    for i in range(START_INDEX, len(blockchain)):

        if i == 0:
            blockchain[i]["previous_hash"] = "0"
        else:
            blockchain[i]["previous_hash"] = blockchain[i - 1]["hash"]

        old_hash = blockchain[i].get("hash", "")
        old_nonce = blockchain[i].get("nonce", None)

        new_hash, new_nonce, elapsed_time = mine_block(
            blockchain[i],
            DIFFICULTY,
            MAX_NONCE
        )

        blockchain[i]["hash"] = new_hash

        print(
            "block",
            i,
            "re-mined",
            "old_nonce =",
            old_nonce,
            "new_nonce =",
            new_nonce,
            "old_hash =",
            old_hash,
            "new_hash =",
            new_hash,
            "time =",
            round(elapsed_time, 6),
            "sec"
        )

    total_end_time = time.perf_counter()
    total_elapsed_time = total_end_time - total_start_time

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            blockchain,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=== PoW chain repair completed ===")
    print("input file   :", INPUT_FILE)
    print("output file  :", OUTPUT_FILE)
    print("start index  :", START_INDEX)
    print("difficulty   :", DIFFICULTY)
    print("re-mined from:", START_INDEX)
    print("re-mined to  :", len(blockchain) - 1)
    print("total blocks :", len(blockchain) - START_INDEX)
    print("elapsed time :", round(total_elapsed_time, 6), "sec")
    print("note         : hashes and nonces were recalculated from the tampered point onward")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
