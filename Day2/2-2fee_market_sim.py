#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import csv
import matplotlib.pyplot as plt

random.seed(42)

num_blocks = *__*
tx_per_block_limit = *__*
new_tx_per_block = *__*

selection_mode = *__*

output_csv = "2-2fee_market_result.csv"
output_mempool_csv = "2-2mempool_size_result.csv"

waiting_blocks_line_png = "2-2waiting_blocks_line.png"
fee_vs_waiting_blocks_png = "2-2fee_vs_waiting_blocks.png"
tx_size_vs_waiting_blocks_png = "2-2tx_size_vs_waiting_blocks.png"
fee_per_size_vs_waiting_blocks_png = "2-2fee_per_size_vs_waiting_blocks.png"
mempool_size_line_png = "2-2mempool_size_line.png"

mempool = []
tx_id_counter = 1
confirmed_results = []
mempool_size_results = []

valid_modes = [
    "fee_priority",
    "random",
    "small_size_priority",
    "fee_per_size_priority"
]

if selection_mode not in valid_modes:
    print("エラー: selection_mode が不正です。")
    print(valid_modes)
    exit()

for block_height in range(1, num_blocks + 1):

    for i in range(new_tx_per_block):

        fee = random.uniform(*__*, 0.20)
        tx_size = random.randint(200, 2000)
        fee_per_size = fee / *__*

        tx = {
            "tx_id": tx_id_counter,
            "fee": fee,
            "tx_size": tx_size,
            "fee_per_size": fee_per_size,
            "created_block": block_height
        }

        mempool.append(tx)
        tx_id_counter = tx_id_counter + 1

    if selection_mode == "fee_priority":

        mempool.sort(key=lambda x: x["fee"], reverse=True)
        block_txs = mempool[:tx_per_block_limit]
        mempool = mempool[tx_per_block_limit:]

    elif selection_mode == "random":

        if len(mempool) <= tx_per_block_limit:
            block_txs = mempool
            mempool = []
        else:
            block_txs = random.sample(mempool, tx_per_block_limit)

            new_mempool = []

            for tx in mempool:
                selected = False

                for selected_tx in block_txs:
                    if tx["tx_id"] == selected_tx["tx_id"]:
                        selected = True

                if selected == False:
                    new_mempool.append(tx)

            mempool = new_mempool

    elif selection_mode == "small_size_priority":

        mempool.sort(key=lambda x: x["tx_size"])
        block_txs = mempool[:tx_per_block_limit]
        mempool = mempool[tx_per_block_limit:]

    elif selection_mode == "fee_per_size_priority":

        mempool.sort(key=lambda x: x["fee_per_size"], reverse=True)
        block_txs = mempool[:tx_per_block_limit]
        mempool = mempool[tx_per_block_limit:]

    print("Block", block_height)
    print("selection_mode =", selection_mode)

    for tx in block_txs:
        waiting_blocks = block_height - tx["created_block"]

        print(
            "  Tx",
            tx["tx_id"],
            "fee=",
            round(tx["fee"], 4),
            "tx_size=",
            tx["tx_size"],
            "fee_per_size=",
            round(tx["fee_per_size"], 8),
            "waiting_blocks=",
            waiting_blocks
        )

        confirmed_results.append([
            selection_mode,
            tx["tx_id"],
            tx["fee"],
            tx["tx_size"],
            tx["fee_per_size"],
            tx["created_block"],
            block_height,
            waiting_blocks
        ])

    mempool_size_results.append([
        block_height,
        len(mempool)
    ])

    print("  mempool size =", len(mempool))
    print()

total_fee = 0.0
total_tx_size = 0.0
total_fee_per_size = 0.0
total_waiting_blocks = 0.0

high_fee_wait = 0.0
low_fee_wait = 0.0
high_fee_count = 0
low_fee_count = 0

small_size_wait = 0.0
large_size_wait = 0.0
small_size_count = 0
large_size_count = 0

for row in confirmed_results:
    fee = row[2]
    tx_size = row[3]
    fee_per_size = row[4]
    waiting_blocks = row[7]

    total_fee = total_fee + fee
    total_tx_size = total_tx_size + tx_size
    total_fee_per_size = total_fee_per_size + fee_per_size
    total_waiting_blocks = total_waiting_blocks + waiting_blocks

    if fee >= *__*:
        high_fee_wait = high_fee_wait + waiting_blocks
        high_fee_count = high_fee_count + 1
    else:
        low_fee_wait = low_fee_wait + waiting_blocks
        low_fee_count = low_fee_count + 1

    if tx_size <= 1000:
        small_size_wait = small_size_wait + waiting_blocks
        small_size_count = small_size_count + 1
    else:
        large_size_wait = large_size_wait + waiting_blocks
        large_size_count = large_size_count + 1

confirmed_count = len(confirmed_results)

average_fee = total_fee / confirmed_count
average_tx_size = total_tx_size / confirmed_count
average_fee_per_size = total_fee_per_size / confirmed_count
average_waiting_blocks = total_waiting_blocks / *__*

print("=== 手数料市場シミュレーション結果 ===")
print("selection_mode =", selection_mode)
print("num_blocks =", num_blocks)
print("tx_per_block_limit =", tx_per_block_limit)
print("new_tx_per_block =", new_tx_per_block)
print("confirmed tx count =", confirmed_count)
print("remaining mempool size =", len(mempool))
print("average fee =", average_fee)
print("average tx_size =", average_tx_size)
print("average fee_per_size =", average_fee_per_size)
print("average waiting blocks =", average_waiting_blocks)

if *__* > 0:
    print("high fee tx average waiting blocks =", high_fee_wait / high_fee_count)

if low_fee_count > 0:
    print("low fee tx average waiting blocks =", low_fee_wait / low_fee_count)

if small_size_count > 0:
    print("small size tx average waiting blocks =", small_size_wait / small_size_count)

if large_size_count > 0:
    print("large size tx average waiting blocks =", large_size_wait / large_size_count)

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "selection_mode",
        "tx_id",
        "fee",
        "tx_size",
        "fee_per_size",
        "created_block",
        "confirmed_block",
        "waiting_blocks"
    ])

    for row in confirmed_results:
        writer.writerow(row)

print("CSVを保存:", output_csv)

with open(output_mempool_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "block_height",
        "mempool_size"
    ])

    for row in mempool_size_results:
        writer.writerow(row)

print("CSVを保存:", *__*)

tx_ids = []
fees = []
tx_sizes = []
fee_per_sizes = []
waiting_blocks_list = []

for row in confirmed_results:
    tx_ids.append(row[1])
    fees.append(row[2])
    tx_sizes.append(row[3])
    fee_per_sizes.append(row[4])
    waiting_blocks_list.append(row[7])

block_heights = []
mempool_sizes = []

for row in mempool_size_results:
    block_heights.append(row[0])
    mempool_sizes.append(row[1])

plt.figure(figsize=(10, 5))
plt.plot(*__*, *__*)
plt.xlabel("Tx ID")
plt.ylabel("Waiting Blocks")
plt.title("Waiting Blocks per Tx (" + selection_mode + ")")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存しました:", waiting_blocks_line_png)

plt.figure(figsize=(10, 5))
plt.scatter(*__*, *__*)
plt.xlabel("Fee")
plt.ylabel("Waiting Blocks")
plt.title("Fee vs Waiting Blocks (" + selection_mode + ")")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", fee_vs_waiting_blocks_png)

plt.figure(figsize=(10, 5))
plt.scatter(*__*, *__*)
plt.xlabel("Tx Size [bytes]")
plt.ylabel("Waiting Blocks")
plt.title("Tx Size vs Waiting Blocks (" + selection_mode + ")")
plt.grid(True)
plt.tight_layout()
plt.savefig(tx_size_vs_waiting_blocks_png)
plt.close()

print("グラフを保存:", tx_size_vs_waiting_blocks_png)

plt.figure(figsize=(10, 5))
plt.scatter(fee_per_sizes, waiting_blocks_list)
plt.xlabel("Fee per Size")
plt.ylabel("Waiting Blocks")
plt.title("Fee per Size vs Waiting Blocks (" + selection_mode + ")")
plt.grid(True)
plt.tight_layout()
plt.savefig(fee_per_size_vs_waiting_blocks_png)
plt.close()

print("グラフを保存:", fee_per_size_vs_waiting_blocks_png)

plt.figure(figsize=(10, 5))
plt.plot(block_heights, mempool_sizes)
plt.xlabel("Block Height")
plt.ylabel("Mempool Size")
plt.title("Mempool Size per Block (" + selection_mode + ")")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", mempool_size_line_png)