#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


# ============================================================
# CONFIG: 主にここを編集
# ============================================================
OUTPUT_FILE = Path("blockchain_1000_pow5.json")
BLOCK_COUNT = 1000

# difficulty は「先頭ゼロの個数」
# 例:
#   difficulty = 3 -> hash が "000..." で始まる必要がある
DIFFICULTY = 5

# 進捗表示間隔
PROGRESS_INTERVAL = 100
# ============================================================


def calculate_hash(
    index: int,
    timestamp: float,
    data: str,
    previous_hash: str,
    nonce: int,
) -> str:
    raw = f"{index}|{timestamp}|{data}|{previous_hash}|{nonce}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mine_block(
    index: int,
    timestamp: float,
    data: str,
    previous_hash: str,
    difficulty: int,
) -> tuple[int, str, float]:
    prefix = "0" * difficulty
    nonce = 0

    start_time = time.perf_counter()

    while True:
        block_hash = calculate_hash(
            index=index,
            timestamp=timestamp,
            data=data,
            previous_hash=previous_hash,
            nonce=nonce,
        )

        if block_hash.startswith(prefix):
            end_time = time.perf_counter()
            mining_time = end_time - start_time
            return nonce, block_hash, mining_time

        nonce += 1


def create_genesis_block(difficulty: int) -> dict:
    index = 0
    timestamp = time.time()
    data = "Genesis Block"
    previous_hash = "0" * 64

    nonce, block_hash, mining_time = mine_block(
        index=index,
        timestamp=timestamp,
        data=data,
        previous_hash=previous_hash,
        difficulty=difficulty,
    )

    return {
        "index": index,
        "timestamp": timestamp,
        "data": data,
        "previous_hash": previous_hash,
        "difficulty": difficulty,
        "nonce": nonce,
        "mining_time_seconds": mining_time,
        "hash": block_hash,
    }


def create_next_block(previous_block: dict, data: str, difficulty: int) -> dict:
    index = previous_block["index"] + 1
    timestamp = time.time()
    previous_hash = previous_block["hash"]

    nonce, block_hash, mining_time = mine_block(
        index=index,
        timestamp=timestamp,
        data=data,
        previous_hash=previous_hash,
        difficulty=difficulty,
    )

    return {
        "index": index,
        "timestamp": timestamp,
        "data": data,
        "previous_hash": previous_hash,
        "difficulty": difficulty,
        "nonce": nonce,
        "mining_time_seconds": mining_time,
        "hash": block_hash,
    }


def main() -> int:
    chain: list[dict] = []

    total_start = time.perf_counter()

    genesis = create_genesis_block(DIFFICULTY)
    chain.append(genesis)

    print("=== mining start ===")
    print(f"output file : {OUTPUT_FILE}")
    print(f"block count : {BLOCK_COUNT}")
    print(f"difficulty  : {DIFFICULTY}")
    print()

    print(
        f"[0/{BLOCK_COUNT - 1}] "
        f"nonce={genesis['nonce']} "
        f"time={genesis['mining_time_seconds']:.6f}s "
        f"hash={genesis['hash']}"
    )

    for i in range(1, BLOCK_COUNT):
        data = f"Block {i} data"
        new_block = create_next_block(chain[-1], data, DIFFICULTY)
        chain.append(new_block)

        if i % PROGRESS_INTERVAL == 0 or i == BLOCK_COUNT - 1:
            print(
                f"[{i}/{BLOCK_COUNT - 1}] "
                f"nonce={new_block['nonce']} "
                f"time={new_block['mining_time_seconds']:.6f}s "
                f"hash={new_block['hash']}"
            )

    total_end = time.perf_counter()
    total_elapsed = total_end - total_start

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(chain, f, ensure_ascii=False, indent=2)

    total_mining_time = sum(block["mining_time_seconds"] for block in chain)
    avg_mining_time = total_mining_time / len(chain) if chain else 0.0

    print()
    print("=== mining completed ===")
    print(f"saved file           : {OUTPUT_FILE}")
    print(f"generated blocks     : {len(chain)}")
    print(f"difficulty           : {DIFFICULTY}")
    print(f"first block hash     : {chain[0]['hash']}")
    print(f"last block hash      : {chain[-1]['hash']}")
    print(f"total mining time    : {total_mining_time:.6f} seconds")
    print(f"average mining time  : {avg_mining_time:.6f} seconds")
    print(f"total elapsed time   : {total_elapsed:.6f} seconds")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())