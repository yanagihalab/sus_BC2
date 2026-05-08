#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import csv
import matplotlib.pyplot as plt

random.seed(42)

num_transfers = *__*

chain_a_average_block_time = *__*
chain_b_average_block_time = *__*

relayer_average_delay = *__*

output_csv = "2-4ibc_transfer_delay_result.csv"

output_total_delay_line_png = "2-4total_delay_line.png"
output_delay_components_line_png = "2-4delay_components_line.png"
output_total_delay_hist_png = "2-4total_delay_hist.png"
output_average_delay_bar_png = "2-4average_delay_bar.png"
output_delay_components_stacked_bar_png = "2-4delay_components_stacked_bar.png"
output_relayer_vs_total_png = "2-4relayer_vs_total.png"
output_chain_a_vs_total_png = "2-4chain_a_vs_total.png"
output_chain_b_vs_total_png = "2-4chain_b_vs_total.png"
output_cumulative_average_delay_png = "2-4cumulative_average_delay.png"
output_boxplot_delay_components_png = "2-4boxplot_delay_components.png"

results = []

total_delay = 0.0
total_chain_a_wait = 0.0
total_relayer_delay = 0.0
total_chain_b_wait = 0.0

for transfer_id in range(1, num_transfers + 1):

    chain_a_wait = random.uniform(
        chain_a_average_block_time * 0.5,
        chain_a_average_block_time * 1.5
    )

    relayer_delay = random.uniform(
        relayer_average_delay * 0.5,
        relayer_average_delay * 1.5
    )

    chain_b_wait = random.uniform(
        chain_b_average_block_time * 0.5,
        chain_b_average_block_time * 1.5
    )

    total_transfer_delay = chain_a_wait + relayer_delay + chain_b_wait

    total_delay = total_delay + total_transfer_delay
    total_chain_a_wait = total_chain_a_wait + chain_a_wait
    total_relayer_delay = total_relayer_delay + relayer_delay
    total_chain_b_wait = total_chain_b_wait + chain_b_wait

    results.append([
        transfer_id,
        chain_a_wait,
        relayer_delay,
        chain_b_wait,
        total_transfer_delay
    ])

    print(
        "Transfer",
        transfer_id,
        "ChainA_wait=",
        round(chain_a_wait, 3),
        "Relayer_delay=",
        round(relayer_delay, 3),
        "ChainB_wait=",
        round(chain_b_wait, 3),
        "Total=",
        round(total_transfer_delay, 3)
    )

average_chain_a_wait = total_chain_a_wait / *__*
average_relayer_delay = total_relayer_delay / num_transfers
average_chain_b_wait = total_chain_b_wait / num_transfers
average_total_delay = total_delay / num_transfers

print()
print("=== IBC転送遅延シミュレーション結果 ===")
print("num_transfers =", num_transfers)
print("average_chain_a_wait =", average_chain_a_wait)
print("average_relayer_delay =", average_relayer_delay)
print("average_chain_b_wait =", average_chain_b_wait)
print("average_total_delay =", average_total_delay)

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "transfer_id",
        "chain_a_wait",
        "relayer_delay",
        "chain_b_wait",
        "total_transfer_delay"
    ])

    for row in results:
        writer.writerow(row)

print("CSVを保存しました:", output_csv)

transfer_ids = []
chain_a_waits = []
relayer_delays = []
chain_b_waits = []
total_transfer_delays = []

for row in results:
    transfer_ids.append(row[0])
    chain_a_waits.append(row[1])
    relayer_delays.append(row[2])
    chain_b_waits.append(row[3])
    total_transfer_delays.append(row[4])

plt.figure(figsize=(10, 5))
plt.plot(transfer_ids, total_transfer_delays)
plt.xlabel("Transfer ID")
plt.ylabel("Total Transfer Delay [seconds]")
plt.title("Total IBC Transfer Delay per Transfer")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存しました:", output_total_delay_line_png)

plt.figure(figsize=(10, 5))
plt.plot(transfer_ids, chain_a_waits, label="Chain A Wait")
plt.plot(transfer_ids, relayer_delays, label="Relayer Delay")
plt.plot(transfer_ids, chain_b_waits, label="Chain B Wait")
plt.xlabel("Transfer ID")
plt.ylabel("Delay [seconds]")
plt.title("Delay Components per Transfer")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存しました:", output_delay_components_line_png)

plt.figure(figsize=(10, 5))
plt.hist(total_transfer_delays, bins=*__*)
plt.xlabel("Total Transfer Delay [seconds]")
plt.ylabel("Frequency")
plt.title("Histogram of Total IBC Transfer Delay")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_total_delay_hist_png)
plt.close()

print("グラフを保存しました:", output_total_delay_hist_png)

average_values = [
    average_chain_a_wait,
    average_relayer_delay,
    average_chain_b_wait
]

labels = [
    "Chain A Wait",
    "Relayer Delay",
    "Chain B Wait"
]

plt.figure(figsize=(8, 5))
plt.bar(labels, average_values)
plt.xlabel("Component")
plt.ylabel("Average Delay [seconds]")
plt.title("Average Delay Components")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_average_delay_bar_png)
plt.close()

print("グラフを保存しました:", output_average_delay_bar_png)

bottom_for_relayer = []

for value in chain_a_waits:
    bottom_for_relayer.append(value)

bottom_for_chain_b = []

for i in range(len(chain_a_waits)):
    bottom_for_chain_b.append(chain_a_waits[i] + relayer_delays[i])

plt.figure(figsize=(14, 6))
plt.bar(transfer_ids, chain_a_waits, label="Chain A Wait")
plt.bar(transfer_ids, relayer_delays, bottom=bottom_for_relayer, label="Relayer Delay")
plt.bar(transfer_ids, chain_b_waits, bottom=bottom_for_chain_b, label="Chain B Wait")
plt.xlabel("Transfer ID")
plt.ylabel("Delay [seconds]")
plt.title("Stacked Delay Components per IBC Transfer")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(output_delay_components_stacked_bar_png)
plt.close()

print("グラフを保存しました:", output_delay_components_stacked_bar_png)

plt.figure(figsize=(8, 5))
plt.scatter(relayer_delays, total_transfer_delays)
plt.xlabel("Relayer Delay [seconds]")
plt.ylabel("Total Transfer Delay [seconds]")
plt.title("Relayer Delay vs Total Transfer Delay")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_relayer_vs_total_png)
plt.close()

print("グラフを保存しました:", output_relayer_vs_total_png)

plt.figure(figsize=(8, 5))
plt.scatter(chain_a_waits, total_transfer_delays)
plt.xlabel("Chain A Wait [seconds]")
plt.ylabel("Total Transfer Delay [seconds]")
plt.title("Chain A Wait vs Total Transfer Delay")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_chain_a_vs_total_png)
plt.close()

print("グラフを保存しました:", output_chain_a_vs_total_png)

plt.figure(figsize=(8, 5))
plt.scatter(chain_b_waits, total_transfer_delays)
plt.xlabel("Chain B Wait [seconds]")
plt.ylabel("Total Transfer Delay [seconds]")
plt.title("Chain B Wait vs Total Transfer Delay")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_chain_b_vs_total_png)
plt.close()

print("グラフを保存しました:", output_chain_b_vs_total_png)

cumulative_average_delays = []
cumulative_sum = 0.0

for i in range(len(total_transfer_delays)):
    cumulative_sum = cumulative_sum + total_transfer_delays[i]
    cumulative_average = cumulative_sum / *__*
    cumulative_average_delays.append(cumulative_average)

plt.figure(figsize=(10, 5))
plt.plot(transfer_ids, cumulative_average_delays)
plt.xlabel("Transfer ID")
plt.ylabel("Cumulative Average Delay [seconds]")
plt.title("Cumulative Average IBC Transfer Delay")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存しました:", output_cumulative_average_delay_png)

plt.figure(figsize=(8, 5))
plt.boxplot([
    chain_a_waits,
    relayer_delays,
    chain_b_waits,
    total_transfer_delays
], labels=[
    "Chain A",
    "Relayer",
    "Chain B",
    "Total"
])
plt.ylabel("Delay [seconds]")
plt.title("Boxplot of IBC Delay Components")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存しました:", output_boxplot_delay_components_png)