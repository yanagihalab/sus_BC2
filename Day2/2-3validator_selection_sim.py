#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import csv
import matplotlib.pyplot as *__*

random.seed(42)

num_blocks = *__*
num_validators = *__*

voting_power_mode = *__*

pareto_alpha = *__*
min_voting_power = 1
pareto_scale = 100

nakamoto_threshold_ratio = 1.0 / 3.0

output_block_csv = "2-3validator_selection_blocks_250nodes.csv"
output_summary_csv = "2-3validator_selection_summary_250nodes.csv"
output_global_csv = "2-3validator_selection_global_stats_250nodes.csv"

output_voting_power_transition_png = "2-3voting_power_transition.png"
output_voting_power_rank_png = "2-3voting_power_rank_distribution.png"
output_cumulative_voting_power_png = "2-3cumulative_voting_power.png"
output_proposer_count_png = "2-3proposer_count_top20.png"
output_consecutive_count_png = "2-3consecutive_count_top20.png"

if num_validators < 1:
    print("エラー: num_validators は1以上にしてください。")
    exit()

if num_validators > 250:
    print("エラー: num_validators は最大250までです。")
    exit()

if num_blocks < 1:
    print("エラー: num_blocks は1以上にしてください。")
    exit()

if voting_power_mode != "equal" and \
   voting_power_mode != "random" and \
   voting_power_mode != "top_heavy" and \
   voting_power_mode != "pareto":
    print("エラー: voting_power_mode が不正です。")
    print("equal, random, top_heavy, pareto のいずれかを指定してください。")
    exit()

if pareto_alpha <= 0:
    print("エラー: pareto_alpha は0より大きくしてください。")
    exit()

if nakamoto_threshold_ratio <= 0 or nakamoto_threshold_ratio >= 1:
    print("エラー: nakamoto_threshold_ratio は0より大きく1未満にしてください。")
    exit()

validators = []
voting_powers = []

for i in range(1, num_validators + 1):

    validator_name = "validator_" + str(i)
    validators.append(validator_name)

    if voting_power_mode == "equal":
        power = 10

    elif voting_power_mode == "random":
        power = random.randint(1, 100)

    elif voting_power_mode == "top_heavy":
        power = num_validators - i + 1

    elif voting_power_mode == "pareto":
        pareto_value = random.paretovariate(*__*)
        power = int(pareto_value * pareto_scale)

        if power < min_voting_power:
            power = min_voting_power

    voting_powers.append(power)

total_voting_power = 0

for power in voting_powers:
    total_voting_power = total_voting_power + power

validator_power_dict = {}

for i in range(len(validators)):
    validator_power_dict[validators[i]] = voting_powers[i]

validator_power_list = []

for i in range(len(validators)):
    validator_power_list.append([
        validators[i],
        voting_powers[i]
    ])

validator_power_list.sort(key=lambda x: x[1], reverse=True)

nakamoto_threshold_power = total_voting_power * *__*

nakamoto_coefficient = 0
nakamoto_power_sum = 0
nakamoto_validators = []

for row in validator_power_list:

    validator_name = row[0]
    voting_power = row[1]

    nakamoto_power_sum = nakamoto_power_sum + voting_power
    nakamoto_coefficient = nakamoto_coefficient + 1
    nakamoto_validators.append(validator_name)

    if nakamoto_power_sum > nakamoto_threshold_power:
        break

nakamoto_power_ratio = nakamoto_power_sum / total_voting_power

results = []

proposal_counts = {}
consecutive_counts = {}

for name in validators:
    proposal_counts[name] = 0
    consecutive_counts[name] = 0

total_consecutive_count = 0
previous_validator = ""

for block_height in range(1, num_blocks + 1):

    proposer = random.choices(
        validators,
        weights=voting_powers,
        k=1
    )[0]

    proposer_voting_power = validator_power_dict[proposer]

    proposal_counts[proposer] = proposal_counts[proposer] + 1

    is_consecutive = 0

    if proposer == previous_validator:
        total_consecutive_count = total_consecutive_count + 1
        consecutive_counts[proposer] = consecutive_counts[proposer] + 1
        is_consecutive = 1

    previous_validator = proposer

    results.append([
        block_height,
        proposer,
        proposer_voting_power,
        is_consecutive
    ])

    print(
        "Block",
        block_height,
        "proposer =",
        proposer,
        "voting_power =",
        proposer_voting_power,
        "consecutive =",
        is_consecutive
    )

summary_results = []

for i in range(len(validators)):

    validator_name = validators[i]
    voting_power = voting_powers[i]

    expected_ratio = voting_power / total_voting_power
    actual_proposals = proposal_counts[validator_name]
    actual_ratio = actual_proposals / num_blocks
    ratio_difference = actual_ratio - expected_ratio

    summary_results.append([
        validator_name,
        voting_power,
        expected_ratio,
        actual_proposals,
        actual_ratio,
        ratio_difference,
        consecutive_counts[validator_name]
    ])

summary_by_power = []

for row in summary_results:
    summary_by_power.append(row)

summary_by_power.sort(key=lambda x: x[1], reverse=True)

summary_by_proposals = []

for row in summary_results:
    summary_by_proposals.append(row)

summary_by_proposals.sort(key=lambda x: x[3], reverse=True)

top1_power = 0
top3_power = 0
top5_power = 0
top10_power = 0
top20_power = 0

for i in range(len(summary_by_power)):

    if i < 1:
        top1_power = top1_power + summary_by_power[i][1]

    if i < 3:
        top3_power = top3_power + summary_by_power[i][1]

    if i < 5:
        top5_power = top5_power + summary_by_power[i][1]

    if i < 10:
        top10_power = top10_power + summary_by_power[i][1]

    if i < 20:
        top20_power = top20_power + summary_by_power[i][1]

top1_power_ratio = top1_power / total_voting_power
top3_power_ratio = top3_power / total_voting_power
top5_power_ratio = top5_power / total_voting_power
top10_power_ratio = top10_power / total_voting_power
top20_power_ratio = top20_power / total_voting_power

top1_proposals = 0
top3_proposals = 0
top5_proposals = 0
top10_proposals = 0
top20_proposals = 0

for i in range(len(summary_by_proposals)):

    if i < 1:
        top1_proposals = top1_proposals + summary_by_proposals[i][3]

    if i < 3:
        top3_proposals = top3_proposals + summary_by_proposals[i][3]

    if i < 5:
        top5_proposals = top5_proposals + summary_by_proposals[i][3]

    if i < 10:
        top10_proposals = top10_proposals + summary_by_proposals[i][3]

    if i < 20:
        top20_proposals = top20_proposals + summary_by_proposals[i][3]

top1_proposal_ratio = top1_proposals / num_blocks
top3_proposal_ratio = top3_proposals / num_blocks
top5_proposal_ratio = top5_proposals / num_blocks
top10_proposal_ratio = top10_proposals / num_blocks
top20_proposal_ratio = top20_proposals / num_blocks

if num_blocks > 1:
    consecutive_ratio = total_consecutive_count / (num_blocks - 1)
else:
    consecutive_ratio = 0

print()
print("=== バリデータ選出シミュレーション結果 ===")
print("num_validators =", *__*)
print("num_blocks =", num_blocks)
print("voting_power_mode =", voting_power_mode)
print("pareto_alpha =", pareto_alpha)
print("pareto_scale =", pareto_scale)
print("total_voting_power =", total_voting_power)
print()

print("=== Nakamoto Coefficient ===")
print("definition = minimum number of validators required to exceed threshold voting power")
print("threshold_ratio =", *__*)
print("threshold_power =", nakamoto_threshold_power)
print("nakamoto_coefficient =", nakamoto_coefficient)
print("nakamoto_power_sum =", nakamoto_power_sum)
print("nakamoto_power_ratio =", nakamoto_power_ratio)
print("nakamoto_validators =", nakamoto_validators)
print()

print("=== voting power 集中度 ===")
print("top1_power_ratio =", top1_power_ratio)
print("top3_power_ratio =", top3_power_ratio)
print("top5_power_ratio =", top5_power_ratio)
print("top10_power_ratio =", top10_power_ratio)
print("top20_power_ratio =", top20_power_ratio)
print()

print("=== proposer 集中度 ===")
print("total_consecutive_count =", total_consecutive_count)
print("consecutive proposer ratio =", consecutive_ratio)
print("top1 proposer ratio =", top1_proposal_ratio)
print("top3 proposer ratio =", *__*)
print("top5 proposer ratio =", top5_proposal_ratio)
print("top10 proposer ratio =", top10_proposal_ratio)
print("top20 proposer ratio =", *__*)
print()

print("=== voting power 上位10 validator ===")

display_count = 10

if num_validators < 10:
    display_count = num_validators

for i in range(display_count):

    row = summary_by_power[i]

    print(
        i + 1,
        row[0],
        "voting_power =",
        row[1],
        "expected_ratio =",
        round(row[2], 6),
        "actual_proposals =",
        row[3],
        "actual_ratio =",
        round(row[4], 6),
        "ratio_difference =",
        round(row[5], 6),
        "consecutive_count =",
        row[6]
    )

with open(output_block_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "block_height",
        "proposer",
        "proposer_voting_power",
        "is_consecutive"
    ])

    for row in results:
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

    for row in summary_by_power:
        writer.writerow(row)

print("CSVを保存:", output_summary_csv)

with open(output_global_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "num_validators",
        "num_blocks",
        "voting_power_mode",
        "pareto_alpha",
        "pareto_scale",
        "total_voting_power",
        "nakamoto_threshold_ratio",
        "nakamoto_threshold_power",
        "nakamoto_coefficient",
        "nakamoto_power_sum",
        "nakamoto_power_ratio",
        "nakamoto_validators",
        "top1_power_ratio",
        "top3_power_ratio",
        "top5_power_ratio",
        "top10_power_ratio",
        "top20_power_ratio",
        "total_consecutive_count",
        "consecutive_ratio",
        "top1_proposal_ratio",
        "top3_proposal_ratio",
        "top5_proposal_ratio",
        "top10_proposal_ratio",
        "top20_proposal_ratio"
    ])

    writer.writerow([
        num_validators,
        num_blocks,
        voting_power_mode,
        pareto_alpha,
        pareto_scale,
        total_voting_power,
        nakamoto_threshold_ratio,
        nakamoto_threshold_power,
        nakamoto_coefficient,
        nakamoto_power_sum,
        nakamoto_power_ratio,
        " ".join(nakamoto_validators),
        top1_power_ratio,
        top3_power_ratio,
        top5_power_ratio,
        top10_power_ratio,
        top20_power_ratio,
        total_consecutive_count,
        consecutive_ratio,
        top1_proposal_ratio,
        top3_proposal_ratio,
        top5_proposal_ratio,
        top10_proposal_ratio,
        top20_proposal_ratio
    ])

print("CSVを保存:", output_global_csv)

block_heights = []
proposer_voting_powers = []

for row in results:
    block_heights.append(row[0])
    proposer_voting_powers.append(row[2])

plt.figure(figsize=(12, 5))
plt.plot(block_heights, proposer_voting_powers)
plt.xlabel("Block Height")
plt.ylabel("Proposer Voting Power")
plt.title("Transition of Proposer Voting Power")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_voting_power_transition_png)

rank_list = []
voting_power_rank_list = []

for i in range(len(summary_by_power)):
    rank_list.append(i + 1)
    voting_power_rank_list.append(summary_by_power[i][1])

plt.figure(figsize=(12, 5))
plt.plot(rank_list, voting_power_rank_list)
plt.xlabel("Validator Rank by Voting Power")
plt.ylabel("Voting Power")
plt.title("Voting Power Distribution by Rank")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_voting_power_rank_png)
plt.close()

print("グラフを保存:", output_voting_power_rank_png)

cumulative_power = 0
cumulative_power_ratios = []
rank_list_for_cumulative = []

for i in range(len(summary_by_power)):
    cumulative_power = cumulative_power + summary_by_power[i][1]
    cumulative_ratio = cumulative_power / total_voting_power

    rank_list_for_cumulative.append(i + 1)
    cumulative_power_ratios.append(cumulative_ratio)

plt.figure(figsize=(12, 5))
plt.plot(rank_list_for_cumulative, cumulative_power_ratios)
plt.axhline(y=nakamoto_threshold_ratio, linestyle="--")
plt.xlabel("Validator Rank by Voting Power")
plt.ylabel("Cumulative Voting Power Ratio")
plt.title("Cumulative Voting Power Ratio")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_cumulative_voting_power_png)

top_n = *__*

if len(summary_by_proposals) < top_n:
    top_n = len(summary_by_proposals)

top_validator_names = []
top_proposal_counts = []

for i in range(top_n):
    top_validator_names.append(summary_by_proposals[i][0])
    top_proposal_counts.append(summary_by_proposals[i][3])

plt.figure(figsize=(14, 6))
plt.bar(top_validator_names, top_proposal_counts)
plt.xlabel("Validator")
plt.ylabel("Proposal Count")
plt.title("Top Validator Proposal Counts")
plt.xticks(rotation=90)
plt.grid(True)
plt.tight_layout()
plt.savefig(output_proposer_count_png)
plt.close()

print("グラフを保存:", output_proposer_count_png)

summary_by_consecutive = []

for row in summary_results:
    summary_by_consecutive.append(row)

summary_by_consecutive.sort(key=lambda x: x[6], reverse=True)

top_n = 20

if len(summary_by_consecutive) < top_n:
    top_n = len(summary_by_consecutive)

top_consecutive_names = []
top_consecutive_counts = []

for i in range(top_n):
    top_consecutive_names.append(summary_by_consecutive[i][0])
    top_consecutive_counts.append(summary_by_consecutive[i][6])

plt.figure(figsize=(14, 6))
plt.bar(top_consecutive_names, top_consecutive_counts)
plt.xlabel("Validator")
plt.ylabel("Consecutive Proposal Count")
plt.title("Top Validator Consecutive Proposal Counts")
plt.xticks(rotation=90)
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_consecutive_count_png)

