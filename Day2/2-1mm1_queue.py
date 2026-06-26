
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import csv
import matplotlib.pyplot as plt

arrival_rate = *__*
service_rate = *__*
num_customers = 1000

output_csv = "queue_result.csv"

waiting_time_sec_line_png = "2-1waiting_time_seconds_line.png"
waiting_time_min_line_png = "2-1waiting_time_minutes_line.png"

waiting_time_sec_hist_png = "2-1waiting_time_seconds_hist.png"
waiting_time_min_hist_png = "2-1waiting_time_minutes_hist.png"

system_time_sec_line_png = "2-1system_time_seconds_line.png"
system_time_min_line_png = "2-1system_time_minutes_line.png"

random.seed(42)

current_time = 0.0
server_available_time = 0.0

total_waiting_time = 0.0
total_system_time = 0.0

results = []

customer_ids = []

waiting_times_seconds = []
waiting_times_minutes = []

system_times_seconds = []
system_times_minutes = []

arrival_times_seconds = []
arrival_times_minutes = []

for customer_id in range(1, num_customers + 1):

    inter_arrival_time = random.expovariate(*__*)
    service_time = random.expovariate(*__*)

    arrival_time = current_time + inter_arrival_time

    if arrival_time > server_available_time:
        service_start_time = arrival_time
    else:
        service_start_time = *__*

    waiting_time = service_start_time - *__*
    departure_time = service_start_time + service_time
    system_time = *__* - arrival_time

    server_available_time = *__*
    current_time = arrival_time

    total_waiting_time = total_waiting_time + waiting_time
    total_system_time = total_system_time + system_time

    arrival_time_min = arrival_time / 60.0
    service_start_time_min = *__* / 60.0
    service_time_min = service_time / 60.0
    waiting_time_min = waiting_time / *__*
    departure_time_min = departure_time / 60.0
    system_time_min = system_time / 60.0

    results.append([
        customer_id,
        arrival_time,
        service_start_time,
        service_time,
        waiting_time,
        departure_time,
        system_time,
        arrival_time_min,
        service_start_time_min,
        service_time_min,
        waiting_time_min,
        departure_time_min,
        system_time_min
    ])

    customer_ids.append(customer_id)

    waiting_times_seconds.append(waiting_time)
    waiting_times_minutes.append(waiting_time_min)

    system_times_seconds.append(system_time)
    system_times_minutes.append(system_time_min)

    arrival_times_seconds.append(arrival_time)
    arrival_times_minutes.append(arrival_time_min)

average_waiting_time_seconds = total_waiting_time / *__*
average_system_time_seconds = *__* / num_customers

average_waiting_time_minutes = average_waiting_time_seconds / 60.0
average_system_time_minutes = average_system_time_seconds / 60.0

print("=== M/M/1 待ち行列シミュレーション ===")
print("到着率 λ =", *__*, "件/秒")
print("サービス率 μ =", *__*, "件/秒")
print("客数 =", *__*)
print()

print("平均待ち時間 =", *__*, "秒")
print("平均待ち時間 =", *__*, "分")
print()

print("平均滞在時間 =", *__*, "秒")
print("平均滞在時間 =", *__*, "分")

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "customer_id",

        "arrival_time_seconds",
        "service_start_time_seconds",
        "service_time_seconds",
        "waiting_time_seconds",
        "departure_time_seconds",
        "system_time_seconds",

        "arrival_time_minutes",
        "service_start_time_minutes",
        "service_time_minutes",
        "waiting_time_minutes",
        "departure_time_minutes",
        "system_time_minutes"
    ])

    for row in results:
        writer.writerow(row)

print("CSVを保存:", output_csv)

plt.figure(figsize=(10, 5))
plt.plot(customer_ids, waiting_times_seconds)
plt.xlabel("Customer ID")
plt.ylabel("Waiting Time [seconds]")
plt.title("Waiting Time per Customer [seconds]")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", waiting_time_sec_line_png)

plt.figure(figsize=(10, 5))
plt.plot(customer_ids, waiting_times_minutes)
plt.xlabel("Customer ID")
plt.ylabel("Waiting Time [minutes]")
plt.title("Waiting Time per Customer [minutes]")
plt.grid(True)
plt.tight_layout()
plt.savefig(waiting_time_min_line_png)
plt.close()

print("グラフを保存:", waiting_time_min_line_png)

plt.figure(figsize=(10, 5))
plt.hist(waiting_times_seconds, bins=30)
plt.xlabel("Waiting Time [seconds]")
plt.ylabel("Frequency")
plt.title("Histogram of Waiting Time [seconds]")
plt.grid(True)
plt.tight_layout()
plt.savefig(waiting_time_sec_hist_png)
plt.close()

print("グラフを保存:", waiting_time_sec_hist_png)

plt.figure(figsize=(10, 5))
plt.hist(waiting_times_minutes, bins=30)
plt.xlabel("Waiting Time [minutes]")
plt.ylabel("Frequency")
plt.title("Histogram of Waiting Time [minutes]")
plt.grid(True)
plt.tight_layout()
plt.savefig(waiting_time_min_hist_png)
plt.close()

print("グラフを保存:", waiting_time_min_hist_png)

plt.figure(figsize=(10, 5))
plt.plot(customer_ids, system_times_seconds)
plt.xlabel("Customer ID")
plt.ylabel("System Time [seconds]")
plt.title("System Time per Customer [seconds]")
plt.grid(True)
plt.tight_layout()
plt.savefig(system_time_sec_line_png)
plt.close()

print("グラフを保存:", system_time_sec_line_png)

plt.figure(figsize=(10, 5))
plt.plot(customer_ids, system_times_minutes)
plt.xlabel("Customer ID")
plt.ylabel("System Time [minutes]")
plt.title("System Time per Customer [minutes]")
plt.grid(True)
plt.tight_layout()
plt.savefig(*__*)
plt.close()

print("グラフを保存:", system_time_min_line_png)