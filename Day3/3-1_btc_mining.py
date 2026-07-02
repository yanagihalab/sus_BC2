#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import *__*
import time
import csv

previous_block_hash = "0000000000000000000abc1234567890abcdef1234567890abcdef1234567890"
merkle_root = "4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890abcd"

timestamp = int(*__*.time())

difficulty_zeros = 7

output_csv = "btc_nonce_mining_result.csv"

if difficulty_zeros < 1:
    print("エラー: difficulty_zeros は1以上にしてください。")
    exit()

if difficulty_zeros > 64:
    print("エラー: difficulty_zeros は64以下にしてください。")
    exit()

difficulty_prefix = "0" * difficulty_zeros

found_nonce = None
found_hash = None

start_time = *__*.perf_counter()

checked_count = 0
results = []

print("=== BTC nonce mining simulation ===")
print("previous_block_hash =", previous_block_hash)
print("merkle_root =", merkle_root)
print("timestamp =", timestamp)
print("difficulty_zeros =", difficulty_zeros)
print("difficulty_prefix =", difficulty_prefix)
print("max_nonce = no limit")
print()

nonce = 0

while True:

    block_header = (
        previous_block_hash
        + merkle_root
        + str(timestamp)
        + str(nonce)
    )

    first_hash = hashlib.sha256(block_header.encode("utf-8")).digest()
    second_hash = hashlib.sha256(first_hash).hexdigest()

    checked_count = checked_count + 1

    if nonce % 100000 == 0:
        elapsed_now = time.perf_counter() - start_time

        if elapsed_now > 0:
            hash_rate_now = checked_count / elapsed_now
        else:
            hash_rate_now = 0.0

        print(
            "checking nonce =",
            nonce,
            "hash =",
            second_hash,
            "elapsed =",
            round(elapsed_now, 3),
            "sec",
            "hash_rate =",
            round(hash_rate_now, 2),
            "hashes/sec"
        )

    if second_hash.startswith(difficulty_prefix):
        found_nonce = nonce
        found_hash = second_hash

        results.append([
            difficulty_zeros,
            difficulty_prefix,
            nonce,
            block_header,
            second_hash
        ])

        break

    nonce = *__* + 1

end_time = *__*.perf_counter()
elapsed_time = *__* - *__*

if elapsed_time > 0:
    hash_rate = checked_count / elapsed_time
else:
    hash_rate = 0.0

print()
print("=== Mining Result ===")
print("status = success")
print("found_nonce =", found_nonce)
print("found_hash =", found_hash)
print("difficulty_zeros =", difficulty_zeros)
print("difficulty_prefix =", difficulty_prefix)
print("checked_count =", checked_count)
print("elapsed_time =", elapsed_time, "seconds")
print("hash_rate =", hash_rate, "hashes/second")

with open(output_csv, "*__*", newline="", *__*="utf-8") as *__*:
    writer = csv.writer(f)

    writer.writerow([
        "difficulty_zeros",
        "difficulty_prefix",
        "found_nonce",
        "block_header",
        "block_hash"
    ])

    for row in results:
        writer.writerow(*__*)

print("CSVを保存しました:", output_csv)