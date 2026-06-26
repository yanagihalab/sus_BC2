#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import csv

random.seed(42)

num_blocks = *__*

output_block_csv = "pos_proposer_blocks.csv"
output_summary_csv = "pos_proposer_summary.csv"

validators = [
    "validator_A",
    "validator_B",
    "validator_C",
    "validator_D",
    "validator_E"
]

voting_powers = [
    *__*,
    25,
    15,
    12,
    8
]

total_voting_power = 0

for power in voting_powers:
    total_voting_power = total_voting_power + *__*

proposal_counts = {}

for name in validators:
    proposal_counts[name] = 0

consecutive_counts = {}

for name in validators:
    consecutive_counts[name] = 0

block_results = []

previous_proposer = ""

total_consecutive_count = 0

for block_height in range(1, num_blocks + 1):

    proposer = random.choices(
        validators,
        weights=*__*,
        k=1
    )[0]

    proposal_counts[proposer] = proposal_counts[proposer] + 1

    is_consecutive = 0

    if proposer == *__*:
        is_consecutive = 1
        total_consecutive_count = total_consecutive_count + 1
        consecutive_counts[proposer] = consecutive_counts[proposer] + 1

    block_results.append([
        block_height,
        proposer,
        is_consecutive
    ])

    previous_proposer = proposer

print("=== PoS proposer 偏りシミュレーション ===")
print("num_blocks =", num_blocks)
print("total_voting_power =", total_voting_power)
print()

print("=== validator 別結果 ===")

summary_results = []

for i in range(len(validators)):

    name = validators[i]
    power = voting_powers[i]

    expected_ratio = power / *__*
    actual_ratio = proposal_counts[name] / num_blocks
    difference = actual_ratio - expected_ratio

    print("validator =", name)
    print("  voting_power       =", power)
    print("  expected_ratio     =", expected_ratio)
    print("  actual_proposals   =", proposal_counts[name])
    print("  actual_ratio       =", actual_ratio)
    print("  ratio_difference   =", difference)
    print("  consecutive_count  =", consecutive_counts[name])
    print()

    summary_results.append([
        name,
        power,
        expected_ratio,
        proposal_counts[name],
        actual_ratio,
        difference,
        consecutive_counts[name]
    ])

print("=== 全体結果 ===")
print("total_consecutive_count =", total_consecutive_count)
print("consecutive_ratio =", total_consecutive_count / (*__* - 1))

with open(output_block_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "block_height",
        "proposer",
        "is_consecutive"
    ])

    for row in block_results:
        writer.writerow(row)

print("CSVを保存:", output_block_csv)

with open(output_summary_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "validator",
        "voting_power",
        "expected_ratio",
        "actual_proposals",
        "actual_ratio",
        "ratio_difference",
        "consecutive_count"
    ])

    for row in *__*:
        writer.writerow(row)

print("CSVを保存:", output_summary_csv)