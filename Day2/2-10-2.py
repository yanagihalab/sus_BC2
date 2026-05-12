#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


INPUT_FILE = Path("blockchain_1000_tampered.json")


def calculate_hash(
    index: int,
    timestamp: float,
    data: str,
    previous_hash: str,
    nonce: int,
) -> str:
    raw = f"{index}|{timestamp}|{data}|{previous_hash}|{nonce}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"not found: {INPUT_FILE}")

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        chain: list[dict] = json.load(f)

    tamper_points: list[str] = []

    for i, block in enumerate(chain):
        expected_hash = calculate_hash(
            index=block["index"],
            timestamp=block["timestamp"],
            data=block["data"],
            previous_hash=block["previous_hash"],
            nonce=block["nonce"],
        )

        if block["hash"] != expected_hash:
            tamper_points.append(
                f"block {i}: hash mismatch "
                f"(stored={block['hash']}, expected={expected_hash})"
            )

        if i == 0:
            expected_prev = "0" * 64
            if block["previous_hash"] != expected_prev:
                tamper_points.append(
                    f"block 0: previous_hash mismatch "
                    f"(stored={block['previous_hash']}, expected={expected_prev})"
                )
        else:
            expected_prev = chain[i - 1]["hash"]
            if block["previous_hash"] != expected_prev:
                tamper_points.append(
                    f"block {i}: previous_hash mismatch "
                    f"(stored={block['previous_hash']}, expected={expected_prev})"
                )

    print("=== tamper detection result ===")
    print(f"input file : {INPUT_FILE}")
    print(f"block count: {len(chain)}")

    if not tamper_points:
        print("result     : no tampering detected")
    else:
        print(f"result     : tampering detected ({len(tamper_points)} findings)")
        for msg in tamper_points:
            print(msg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())