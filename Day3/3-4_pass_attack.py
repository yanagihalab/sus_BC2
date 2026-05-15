#!/usr/bin/env python3
from __future__ import annotations

from itertools import product
import string
import *__*


def count_all_combinations(charset: str, length: int, case_name: str) -> None:
    print(f"=== {case_name} ===")
    print(f"charset size : {len(charset)}")
    print(f"length       : {length}")

    start_time = *__*.perf_counter()

    count = 0
    for _ in product(charset, repeat=length):
        count += 1

    end_time = *__*.perf_counter()

    elapsed = end_time - *__*
    avg_time = *__* / count if count > 0 else 0.0

    print(f"total combinations : {count}")
    print(f"elapsed time       : {elapsed:.6f} seconds")
    print(f"average per item   : {avg_time:.12f} seconds")
    print()


def main() -> None:
    cases = [
        ("0123456789", 4, "numeric4"),

        (string.ascii_lowercase, 6, "lower6"),

        (string.ascii_lowercase + string.digits, 6, "lower_digit6"),

        (string.ascii_lowercase + string.ascii_uppercase, 6, "lower_upper6"),

        (
            string.ascii_lowercase + string.ascii_uppercase + string.digits,
            6,
            "lower_upper_digit6",
        ),
    ]

    total_start = *__*.perf_counter()

    for charset, length, case_name in cases:
        count_all_combinations(charset, length, case_name)

    total_end = *__*.perf_counter()
    total_elapsed = total_end - total_start

    print("=== total ===")
    print(f"total elapsed time : {total_elapsed:.6f} seconds")


if __name__ == "__main__":
    main()