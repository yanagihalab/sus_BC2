#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import matplotlib.pyplot as plt

initial_stake = *__*
apr = *__*
simulation_days = *__*
compound_enabled = *__*

output_csv = "staking_reward_result.csv"

output_current_stake_line_png = "current_stake_line.png"
output_total_reward_line_png = "total_reward_line.png"
output_daily_reward_line_png = "daily_reward_line.png"
output_daily_reward_hist_png = "daily_reward_hist.png"
output_stake_and_reward_line_png = "stake_and_reward_line.png"
output_monthly_reward_bar_png = "monthly_reward_bar.png"
output_profit_ratio_line_png = "profit_ratio_line.png"
output_simple_vs_compound_line_png = "simple_vs_compound_line.png"
output_final_stake_bar_png = "final_stake_bar.png"

if initial_stake <= 0:
    print("エラー: initial_stake は0より大きくしてください。")
    exit()

if apr < 0:
    print("エラー: apr は0以上にしてください。")
    exit()

if simulation_days < 1:
    print("エラー: simulation_days は1以上にしてください。")
    exit()

current_stake = initial_stake
total_reward = 0.0

daily_rate = apr / *__*

results = []

days = []
daily_rewards = []
total_rewards = []
current_stakes = []
profit_ratios = []

for day in range(1, simulation_days + 1):

    daily_reward = current_stake * daily_rate

    total_reward = total_reward + daily_reward

    if compound_enabled == True:
        current_stake = current_stake + daily_reward
    else:
        current_stake = *__*

    profit_ratio = total_reward / initial_stake

    results.append([
        day,
        daily_reward,
        total_reward,
        current_stake,
        profit_ratio
    ])

    days.append(day)
    daily_rewards.append(daily_reward)
    total_rewards.append(total_reward)
    current_stakes.append(current_stake)
    profit_ratios.append(profit_ratio)

    if day % 30 == 0 or day == 1 or day == simulation_days:
        print(
            "day =",
            day,
            "daily_reward =",
            round(daily_reward, 6),
            "total_reward =",
            round(total_reward, 6),
            "current_stake =",
            round(current_stake, 6),
            "profit_ratio =",
            round(profit_ratio, 6)
        )

final_stake = current_stake
profit_ratio = total_reward / initial_stake

print()
print("=== ステーキング報酬シミュレーション結果 ===")
print("initial_stake =", initial_stake)
print("apr =", apr)
print("simulation_days =", simulation_days)
print("compound_enabled =", compound_enabled)
print("daily_rate =", daily_rate)
print("total_reward =", total_reward)
print("final_stake =", final_stake)
print("profit_ratio =", profit_ratio)

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "day",
        "daily_reward",
        "total_reward",
        "current_stake",
        "profit_ratio"
    ])

    for row in results:
        writer.writerow(row)

print("CSVを保存:", output_csv)

simple_stake = initial_stake
simple_total_reward = 0.0

compound_stake = initial_stake
compound_total_reward = 0.0

simple_stakes = []
compound_stakes = []
simple_total_rewards = []
compound_total_rewards = []

for day in range(1, simulation_days + 1):

    simple_daily_reward = initial_stake * daily_rate
    simple_total_reward = simple_total_reward + simple_daily_reward
    simple_stake = initial_stake + simple_total_reward

    compound_daily_reward = compound_stake * daily_rate
    compound_total_reward = compound_total_reward + compound_daily_reward
    compound_stake = compound_stake + compound_daily_reward

    simple_stakes.append(simple_stake)
    compound_stakes.append(compound_stake)
    simple_total_rewards.append(simple_total_reward)
    compound_total_rewards.append(compound_total_reward)

monthly_rewards = []
monthly_labels = []

month_index = 1
month_reward_sum = 0.0

for i in range(len(daily_rewards)):
    month_reward_sum = month_reward_sum + daily_rewards[i]

    if (i + 1) % 30 == 0 or (i + 1) == simulation_days:
        monthly_rewards.append(month_reward_sum)
        monthly_labels.append("M" + str(month_index))

        month_index = month_index + 1
        month_reward_sum = 0.0

plt.figure(figsize=(10, 5))
plt.plot(days, current_stakes)
plt.xlabel("Day")
plt.ylabel("Current Stake")
plt.title("Current Stake Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_current_stake_line_png)

plt.figure(figsize=(10, 5))
plt.plot(days, total_rewards)
plt.xlabel("Day")
plt.ylabel("Total Reward")
plt.title("Total Reward Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_total_reward_line_png)
plt.close()

print("グラフを保存:", output_total_reward_line_png)

plt.figure(figsize=(10, 5))
plt.plot(days, daily_rewards)
plt.xlabel("Day")
plt.ylabel("Daily Reward")
plt.title("Daily Reward Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_daily_reward_line_png)
plt.close()

print("グラフを保存:", output_daily_reward_line_png)

plt.figure(figsize=(10, 5))
plt.hist(daily_rewards, bins=*__*)
plt.xlabel("Daily Reward")
plt.ylabel("Frequency")
plt.title("Histogram of Daily Reward")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_daily_reward_hist_png)
plt.close()

print("グラフを保存:", output_daily_reward_hist_png)

plt.figure(figsize=(10, 5))
plt.plot(days, current_stakes, label="Current Stake")
plt.plot(days, total_rewards, label="Total Reward")
plt.xlabel("Day")
plt.ylabel("Amount")
plt.title("Current Stake and Total Reward Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(output_stake_and_reward_line_png)
plt.close()

print("グラフを保存:", output_stake_and_reward_line_png)

plt.figure(figsize=(10, 5))
plt.bar(monthly_labels, monthly_rewards)
plt.xlabel("Month Index")
plt.ylabel("Monthly Reward")
plt.title("Monthly Reward")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_monthly_reward_bar_png)
plt.close()

print("グラフを保存:", output_monthly_reward_bar_png)

plt.figure(figsize=(10, 5))
plt.plot(days, profit_ratios)
plt.xlabel("Day")
plt.ylabel("Profit Ratio")
plt.title("Profit Ratio Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_profit_ratio_line_png)
plt.close()

print("グラフを保存:", output_profit_ratio_line_png)

plt.figure(figsize=(10, 5))
plt.plot(days, simple_stakes, label="Simple")
plt.plot(days, compound_stakes, label="Compound")
plt.xlabel("Day")
plt.ylabel("Stake + Reward")
plt.title("Simple vs Compound Staking")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_simple_vs_compound_line_png)

final_simple_stake = simple_stakes[-1]
final_compound_stake = compound_stakes[-1]

bar_labels = [
    "Initial",
    "Simple Final",
    "Compound Final"
]

bar_values = [
    initial_stake,
    final_simple_stake,
    final_compound_stake
]

plt.figure(figsize=(8, 5))
plt.bar(bar_labels, bar_values)
plt.xlabel("Type")
plt.ylabel("Stake Amount")
plt.title("Initial Stake vs Final Stake")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", output_final_stake_bar_png)