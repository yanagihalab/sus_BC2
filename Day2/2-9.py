#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import time
import csv

# ============================================================
# BTCブロックマイニングのナンス計算 模擬シミュレーション
# difficultyを0の桁数で指定する版
# ============================================================


# ==============================
# 設定
# ==============================

previous_block_hash = "0000000000000000000abc1234567890abcdef1234567890abcdef1234567890"
merkle_root = "4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890abcd"

timestamp = int(time.time())

# 難易度
# ハッシュ先頭に必要な 0 の個数
# 例:
# 3 -> "000"
# 4 -> "0000"
# 5 -> "00000"
difficulty_zeros = 4

# 最大nonce
max_nonce = 10_000_000

output_csv = "btc_nonce_mining_result.csv"


# ==============================
# 入力値チェック
# ==============================

if difficulty_zeros < 1:
    print("エラー: difficulty_zeros は1以上にしてください。")
    exit()

if difficulty_zeros > 64:
    print("エラー: difficulty_zeros は64以下にしてください。")
    exit()

if max_nonce < 0:
    print("エラー: max_nonce は0以上にしてください。")
    exit()


# ==============================
# difficulty prefix生成
# ==============================

difficulty_prefix = "0" * difficulty_zeros


# ==============================
# 初期化
# ==============================

found = False
found_nonce = None
found_hash = None

start_time = time.perf_counter()

checked_count = 0

results = []


# ==============================
# マイニング開始
# ==============================

print("=== BTC nonce mining simulation ===")
print("previous_block_hash =", previous_block_hash)
print("merkle_root =", merkle_root)
print("timestamp =", timestamp)
print("difficulty_zeros =", difficulty_zeros)
print("difficulty_prefix =", difficulty_prefix)
print("max_nonce =", max_nonce)
print()

for nonce in range(max_nonce + 1):

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
        print(
            "checking nonce =",
            nonce,
            "hash =",
            second_hash
        )

    if second_hash.startswith(difficulty_prefix):
        found = True
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


# ==============================
# 結果計算
# ==============================

end_time = time.perf_counter()
elapsed_time = end_time - start_time

if elapsed_time > 0:
    hash_rate = checked_count / elapsed_time
else:
    hash_rate = 0.0


# ==============================
# 結果表示
# ==============================

print()
print("=== Mining Result ===")

if found == True:
    print("status = success")
    print("found_nonce =", found_nonce)
    print("found_hash =", found_hash)
else:
    print("status = failed")
    print("nonce was not found within max_nonce")

print("difficulty_zeros =", difficulty_zeros)
print("difficulty_prefix =", difficulty_prefix)
print("checked_count =", checked_count)
print("elapsed_time =", elapsed_time, "seconds")
print("hash_rate =", hash_rate, "hashes/second")


# ==============================
# CSV出力
# ==============================

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "difficulty_zeros",
        "difficulty_prefix",
        "found_nonce",
        "block_header",
        "block_hash"
    ])

    for row in results:
        writer.writerow(row)

print("CSVを保存しました:", output_csv)