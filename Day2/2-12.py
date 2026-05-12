#!/usr/bin/env python3
from __future__ import annotations

from itertools import product
import string
import time


def count_all_combinations(charset: str, length: int, case_name: str) -> None:
    print(f"=== {case_name} ===")
    print(f"charset size : {len(charset)}")
    print(f"length       : {length}")

    start_time = time.perf_counter()

    count = 0
    for _ in product(charset, repeat=length):
        count += 1

    end_time = time.perf_counter()

    elapsed = end_time - start_time
    avg_time = elapsed / count if count > 0 else 0.0

    print(f"total combinations : {count}")
    print(f"elapsed time       : {elapsed:.6f} seconds")
    print(f"average per item   : {avg_time:.12f} seconds")
    print()


def main() -> None:
    cases = [
        # 例1: 数字4文字
        ("0123456789", 4, "numeric4"),

        # 例2: 英小文字6文字
        (string.ascii_lowercase, 6, "lower6"),

        # 例3: 英小文字+数字6文字
        (string.ascii_lowercase + string.digits, 6, "lower_digit6"),

        # 例4: 英小文字+英大文字6文字
        (string.ascii_lowercase + string.ascii_uppercase, 6, "lower_upper6"),

        # 例5: 英小文字+英大文字+数字6文字
        (
            string.ascii_lowercase + string.ascii_uppercase + string.digits,
            6,
            "lower_upper_digit6",
        ),
    ]

    total_start = time.perf_counter()

    for charset, length, case_name in cases:
        count_all_combinations(charset, length, case_name)

    total_end = time.perf_counter()
    total_elapsed = total_end - total_start

    print("=== total ===")
    print(f"total elapsed time : {total_elapsed:.6f} seconds")


if __name__ == "__main__":
    main()