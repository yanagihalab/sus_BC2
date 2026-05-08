#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import csv
from collections import defaultdict

import matplotlib.pyplot as *__*
from matplotlib.ticker import ScalarFormatter

INPUT_DIR = "current_*__*"
OUT_DIR = "out_*__*_validator_analysis"

PROPOSER_PRIORITY_PLAIN_FIG_WIDTH = 80
PROPOSER_PRIORITY_PLAIN_FIG_HEIGHT = 8


def extract_height_from_filename(filename: str):
    m = re.search(r"BlockNum_(\d+)\.json$", filename)
    if not m:
        return None
    return int(m.group(1))


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def load_validator_files(input_dir: str):
    rows = []

    for name in os.listdir(input_dir):
        if not name.endswith(".json"):
            continue

        path = os.path.join(input_dir, name)
        height = extract_height_from_filename(name)

        if height is None:
            continue

        try:
            with open(path, "*__*", encoding="utf-8") as f:
                data = json.load(*__*)

            *__*.append((height, path, data))

        except Exception as e:
            print(f"[WARN] failed to read {path}: {e}")

    rows.sort(key=lambda x: x[0])
    return rows


def normalize_validators(*__*):
    out = {}

    for v in validators:
        address = v.get("address", "")

        if not address:
            continue

        pub_key = v.get("pub_key", {})
        pub_key_type = pub_key.get("type", "") if isinstance(pub_key, dict) else ""
        pub_key_value = pub_key.get("value", "") if isinstance(pub_key, dict) else ""

        out[address] = {
            "address": address,
            "pub_key_type": pub_key_type,
            "pub_key_value": pub_key_value,
            "voting_power": safe_int(v.get("voting_power", 0)),
            "proposer_priority": safe_int(v.get("proposer_priority", 0)),
        }

    return out


def summarize_validator_presence(*__*):
    stats = defaultdict(lambda: {
        "first_height": None,
        "last_height": None,
        "appearance_count": 0,
        "min_voting_power": None,
        "max_voting_power": None,
        "sum_voting_power": 0,
        "pub_key_type": "",
        "pub_key_value": "",
    })

    for height, _, data in blocks:
        validators = normalize_validators(data.get("validators", []))

        for addr, info in validators.items():
            st = stats[addr]

            if st["first_height"] is None:
                st["first_height"] = height

            st["last_height"] = height
            st["appearance_count"] += 1

            vp = info["voting_power"]

            if st["min_voting_power"] is None or vp < st["min_voting_power"]:
                st["min_voting_power"] = vp

            if st["max_voting_power"] is None or vp > st["max_voting_power"]:
                st["max_voting_power"] = vp

            st["sum_voting_power"] += vp
            st["pub_key_type"] = info["pub_key_type"]
            st["pub_key_value"] = info["pub_key_value"]

    return stats


def analyze_per_height(blocks):
    per_height = []

    for height, path, data in blocks:
        validators = normalize_validators(data.get("validators", []))
        total_voting_power = sum(v["voting_power"] for v in validators.values())

        per_height.append({
            "height": height,
            "file": os.path.basename(path),
            "validator_count": len(validators),
            "total_voting_power": total_voting_power,
        })

    return per_height


def analyze_diffs(blocks):
    diffs = []

    prev_height = None
    prev_validators = None

    for height, _, data in blocks:
        current_validators = normalize_validators(data.get("validators", []))

        if prev_validators is not None:
            prev_set = set(prev_validators.keys())
            curr_set = set(current_validators.keys())

            added = sorted(curr_set - prev_set)
            removed = sorted(prev_set - curr_set)
            common = sorted(prev_set & curr_set)

            power_changed = []
            priority_changed = []

            for addr in common:
                prev_v = prev_validators[addr]
                curr_v = current_validators[addr]

                if prev_v["voting_power"] != curr_v["voting_power"]:
                    power_changed.append({
                        "address": addr,
                        "prev_voting_power": prev_v["voting_power"],
                        "curr_voting_power": curr_v["voting_power"],
                    })

                if prev_v["proposer_priority"] != curr_v["proposer_priority"]:
                    priority_changed.append({
                        "address": addr,
                        "prev_proposer_priority": prev_v["proposer_priority"],
                        "curr_proposer_priority": curr_v["proposer_priority"],
                    })

            diffs.append({
                "prev_height": prev_height,
                "curr_height": height,
                "added_count": len(added),
                "removed_count": len(removed),
                "power_changed_count": len(power_changed),
                "priority_changed_count": len(priority_changed),
                "added": added,
                "removed": removed,
                "power_changed": power_changed,
                "priority_changed": priority_changed,
            })

        prev_height = height
        prev_validators = current_validators

    return diffs


def build_validator_power_timeseries(blocks):
    heights = [height for height, _, _ in blocks]
    address_to_series = defaultdict(list)

    all_addresses = set()
    normalized_by_height = []

    for _, _, data in blocks:
        validators = normalize_validators(data.get("validators", []))
        normalized_by_height.append(validators)
        all_addresses.update(validators.keys())

    all_addresses = sorted(all_addresses)

    for addr in all_addresses:
        address_to_series[addr] = []

    for validators in normalized_by_height:
        current_addresses = set(validators.keys())

        for addr in all_addresses:
            if addr in current_addresses:
                address_to_series[addr].append(validators[addr]["voting_power"])
            else:
                address_to_series[addr].append(None)

    return heights, address_to_series


def build_validator_priority_timeseries(blocks):
    heights = [height for height, _, _ in blocks]
    address_to_series = defaultdict(list)

    all_addresses = set()
    normalized_by_height = []

    for _, _, data in blocks:
        validators = normalize_validators(data.get("validators", []))
        normalized_by_height.append(validators)
        all_addresses.update(validators.keys())

    all_addresses = sorted(all_addresses)

    for addr in all_addresses:
        address_to_series[addr] = []

    for validators in normalized_by_height:
        current_addresses = set(validators.keys())

        for addr in all_addresses:
            if addr in current_addresses:
                address_to_series[addr].append(validators[addr]["proposer_priority"])
            else:
                address_to_series[addr].append(None)

    return heights, address_to_series


def write_presence_csv(stats, out_csv):
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "address",
            "first_height",
            "last_height",
            "appearance_count",
            "avg_voting_power",
            "min_voting_power",
            "max_voting_power",
            "pub_key_type",
            "pub_key_value",
        ])

        for addr, st in sorted(stats.items(), key=lambda x: (-x[1]["appearance_count"], x[0])):
            avg_vp = st["sum_voting_power"] / st["appearance_count"] if st["appearance_count"] else 0

            writer.writerow([
                addr,
                st["first_height"],
                st["last_height"],
                st["appearance_count"],
                f"{avg_vp:.2f}",
                st["min_voting_power"],
                st["max_voting_power"],
                st["pub_key_type"],
                st["pub_key_value"],
            ])


def write_per_height_csv(per_height, *__*):
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "height",
            "file",
            "validator_count",
            "total_voting_power",
        ])

        for row in per_height:
            writer.writerow([
                row["height"],
                row["file"],
                row["validator_count"],
                row["total_voting_power"],
            ])


def write_diff_summary_csv(diffs, out_csv):
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "prev_height",
            "curr_height",
            "added_count",
            "removed_count",
            "power_changed_count",
            "priority_changed_count",
        ])

        for d in diffs:
            writer.writerow([
                d["prev_height"],
                d["curr_height"],
                d["added_count"],
                d["removed_count"],
                d["power_changed_count"],
                d["priority_changed_count"],
            ])


def write_diff_details_json(diffs, out_json):
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(diffs, f, indent=2, ensure_ascii=False)


def shorten_address(addr: str, head=8, tail=6):
    if len(addr) <= head + tail + 3:
        return addr
    return f"{addr[:head]}...{addr[-tail:]}"


def apply_axis_format(use_scientific: bool, axis="both"):
    ax = plt.gca()

    if use_scientific:
        formatter_x = ScalarFormatter(useMathText=False)
        formatter_y = ScalarFormatter(useMathText=False)

        formatter_x.set_scientific(True)
        formatter_y.set_scientific(True)

        formatter_x.set_powerlimits((0, 0))
        formatter_y.set_powerlimits((0, 0))

        if axis in ("x", "both"):
            ax.xaxis.set_major_formatter(formatter_x)
            ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))

        if axis in ("y", "both"):
            ax.yaxis.set_major_formatter(formatter_y)
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    else:
        formatter_x = ScalarFormatter(useOffset=False)
        formatter_y = ScalarFormatter(useOffset=False)

        formatter_x.set_scientific(False)
        formatter_y.set_scientific(False)

        if axis in ("x", "both"):
            ax.xaxis.set_major_formatter(formatter_x)
            ax.ticklabel_format(axis="x", style="plain", useOffset=False)

        if axis in ("y", "both"):
            ax.yaxis.set_major_formatter(formatter_y)
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)


def extract_proposer_maps(blocks):
    *__* = {}
    *__* = {}

    for height, _, data in blocks:
        blockheader = data.get("blockheader", {})
        proposer_address = blockheader.get("proposer_address", "")
        proposer_by_height[height] = proposer_address
        validators_by_height[height] = normalize_validators(data.get("validators", []))

    return proposer_by_height, validators_by_height


def plot_validator_count(per_height, out_path, use_scientific=False):
    heights = [x["height"] for x in per_height]
    counts = [x["validator_count"] for x in per_height]

    plt.figure(figsize=(12, 6))
    plt.plot(heights, counts, marker="o", markersize=2, linewidth=1)
    plt.xlabel("Height")
    plt.ylabel("Validator Count")
    plt.title("Validator Count over Height")
    plt.grid(True)
    apply_axis_format(use_scientific, axis="x")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_validator_set_changes(diffs, out_path, use_scientific=False):
    if not diffs:
        return

    heights = [x["curr_height"] for x in diffs]
    added = [x["added_count"] for x in diffs]
    removed = [x["removed_count"] for x in diffs]
    power_changed = [x["power_changed_count"] for x in diffs]

    plt.figure(figsize=(12, 6))
    plt.plot(heights, added, label="added_count", marker="o", markersize=2, linewidth=1)
    plt.plot(heights, removed, label="removed_count", marker="o", markersize=2, linewidth=1)
    plt.plot(heights, power_changed, label="power_changed_count", marker="o", markersize=2, linewidth=1)
    plt.xlabel("Current Height")
    plt.ylabel("Count")
    plt.title("Validator Set Changes over Height")
    plt.grid(True)
    plt.legend()
    apply_axis_format(use_scientific, axis="x")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_priority_changed_count(diffs, out_path, use_scientific=False):
    if not diffs:
        return

    heights = [x["curr_height"] for x in diffs]
    priority_changed = [x["priority_changed_count"] for x in diffs]

    plt.figure(figsize=(12, 6))
    plt.plot(heights, priority_changed, marker="o", markersize=2, linewidth=1)
    plt.xlabel("Current Height")
    plt.ylabel("Priority Changed Count")
    plt.title("Proposer Priority Changes over Height")
    plt.grid(True)
    apply_axis_format(use_scientific, axis="x")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_all_validators_voting_power(
    blocks,
    stats,
    out_path,
    use_scientific=True,
    fig_width=16,
    fig_height=8
):
    heights, series = build_validator_power_timeseries(blocks)

    ranked_addresses = [
        addr for addr, _ in sorted(
            stats.items(),
            key=lambda x: (-x[1]["appearance_count"], x[0])
        )
    ]

    if not ranked_addresses:
        return

    proposer_by_height, validators_by_height = extract_proposer_maps(blocks)

    plt.figure(figsize=(fig_width, fig_height))

    line_color_by_addr = {}

    for addr in ranked_addresses:
        values = series[addr]
        line, = plt.plot(
            heights,
            values,
            label=shorten_address(addr),
            linewidth=1
        )
        line_color_by_addr[addr] = line.get_color()

    for addr in ranked_addresses:
        marker_heights = []
        marker_values = []

        for height in heights:
            if proposer_by_height.get(height, "") != addr:
                continue

            validators = validators_by_height.get(height, {})
            if addr not in validators:
                continue

            marker_heights.append(height)
            marker_values.append(validators[addr]["voting_power"])

        if marker_heights:
            plt.scatter(
                marker_heights,
                marker_values,
                marker="x",
                s=35,
                linewidths=1.2,
                color=line_color_by_addr.get(addr),
                label=None,
                zorder=5
            )

    plt.xlabel("Height")
    plt.ylabel("Voting Power")
    plt.title("Voting Power over Height")
    plt.grid(True)
    plt.legend(
        fontsize=6,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0.0,
        ncol=1
    )
    apply_axis_format(use_scientific, axis="both")
    plt.tight_layout(rect=[0, 0, 0.82, 1])
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()


def plot_all_validators_proposer_priority(
    blocks,
    stats,
    out_path,
    use_scientific=True,
    fig_width=16,
    fig_height=8
):
    heights, series = build_validator_priority_timeseries(blocks)

    ranked_addresses = [
        addr for addr, _ in sorted(
            stats.items(),
            key=lambda x: (-x[1]["appearance_count"], x[0])
        )
    ]

    if not ranked_addresses:
        return

    proposer_by_height, validators_by_height = extract_proposer_maps(blocks)

    plt.figure(figsize=(fig_width, fig_height))

    line_color_by_addr = {}

    for addr in ranked_addresses:
        values = series[addr]
        line, = plt.plot(
            heights,
            values,
            label=shorten_address(addr),
            linewidth=1
        )
        line_color_by_addr[addr] = line.get_color()

    for addr in ranked_addresses:
        marker_heights = []
        marker_values = []

        for height in heights:
            if proposer_by_height.get(height, "") != addr:
                continue

            validators = validators_by_height.get(height, {})
            if addr not in validators:
                continue

            marker_heights.append(height)
            marker_values.append(validators[addr]["proposer_priority"])

        if marker_heights:
            plt.scatter(
                marker_heights,
                marker_values,
                marker="x",
                s=35,
                linewidths=1.2,
                color=line_color_by_addr.get(addr),
                label=None,
                zorder=5
            )

    plt.xlabel("Height")
    plt.ylabel("Proposer Priority")
    plt.title("Proposer Priority over Height")
    plt.grid(True)
    plt.legend(
        fontsize=6,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0.0,
        ncol=1
    )
    apply_axis_format(use_scientific, axis="both")
    plt.tight_layout(rect=[0, 0, 0.82, 1])
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()


def print_summary(*__*, stats, per_height, diffs):
    print("===== Validator Analysis Summary =====")
    print(f"blocks loaded               : {len(blocks)}")
    print(f"unique validators           : {len(stats)}")

    if per_height:
        counts = [x["validator_count"] for x in per_height]
        totals = [x["total_voting_power"] for x in per_height]

        print(f"validator count min/max     : {min(counts)} / {max(counts)}")
        print(f"total voting power min/max  : {min(totals)} / {max(totals)}")

    added_total = sum(d["added_count"] for d in diffs)
    removed_total = sum(d["removed_count"] for d in diffs)
    power_changed_total = sum(d["power_changed_count"] for d in diffs)
    priority_changed_total = sum(d["priority_changed_count"] for d in diffs)

    print(f"total added events          : {added_total}")
    print(f"total removed events        : {removed_total}")
    print(f"total power changes         : {power_changed_total}")
    print(f"total priority changes      : {priority_changed_total}")
    print()

    print("Top validators by appearance_count")

    ranked = sorted(stats.items(), key=lambda x: (-x[1]["appearance_count"], x[0]))[:10]

    for i, (addr, st) in enumerate(ranked, 1):
        avg_vp = st["sum_voting_power"] / st["appearance_count"] if st["appearance_count"] else 0

        print(
            f"{i:2d}. {addr} "
            f"appear={st['appearance_count']} "
            f"first={st['first_height']} "
            f"last={st['last_height']} "
            f"avg_vp={avg_vp:.2f}"
        )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    blocks = load_validator_files(INPUT_DIR)

    if not blocks:
        print(f"[ERROR] no valid JSON files found in {INPUT_DIR}")
        return 1

    stats = summarize_validator_presence(blocks)
    per_height = analyze_per_height(blocks)
    diffs = analyze_diffs(blocks)

    presence_csv = os.path.join(OUT_DIR, "validator_presence.csv")
    per_height_csv = os.path.join(OUT_DIR, "validator_set_per_height.csv")
    diff_summary_csv = os.path.join(OUT_DIR, "validator_diff_summary.csv")
    diff_details_json = os.path.join(OUT_DIR, "validator_diff_details.json")

    plot_validator_count_path = os.path.join(
        OUT_DIR,
        "validator_count_over_height.png"
    )

    plot_validator_changes_path = os.path.join(
        OUT_DIR,
        "validator_set_changes_over_height.png"
    )

    plot_priority_changed_count_path = os.path.join(
        OUT_DIR,
        "priority_changed_count_over_height.png"
    )

    plot_all_validators_voting_power_scientific_path = os.path.join(
        OUT_DIR,
        "all_validators_voting_power_scientific.png"
    )

    plot_all_validators_voting_power_plain_path = os.path.join(
        OUT_DIR,
        "all_validators_voting_power_plain.png"
    )

    plot_all_validators_proposer_priority_scientific_path = os.path.join(
        OUT_DIR,
        "all_validators_proposer_priority_scientific.png"
    )

    plot_all_validators_proposer_priority_plain_path = os.path.join(
        OUT_DIR,
        "all_validators_proposer_priority_plain.png"
    )

    write_presence_csv(stats, presence_csv)
    write_per_height_csv(per_height, per_height_csv)
    write_diff_summary_csv(diffs, diff_summary_csv)
    write_diff_details_json(diffs, diff_details_json)

    plot_validator_count(
        per_height,
        plot_validator_count_path,
        use_scientific=False
    )

    plot_validator_set_changes(
        diffs,
        plot_validator_changes_path,
        use_scientific=False
    )

    plot_priority_changed_count(
        diffs,
        plot_priority_changed_count_path,
        use_scientific=False
    )

    plot_all_validators_voting_power(
        blocks,
        stats,
        plot_all_validators_voting_power_scientific_path,
        use_scientific=True,
        fig_width=16,
        fig_height=8
    )

    plot_all_validators_voting_power(
        blocks,
        stats,
        plot_all_validators_voting_power_plain_path,
        use_scientific=False,
        fig_width=16,
        fig_height=8
    )

    plot_all_validators_proposer_priority(
        blocks,
        stats,
        plot_all_validators_proposer_priority_scientific_path,
        use_scientific=True,
        fig_width=16,
        fig_height=8
    )

    plot_all_validators_proposer_priority(
        blocks,
        stats,
        plot_all_validators_proposer_priority_plain_path,
        use_scientific=False,
        fig_width=PROPOSER_PRIORITY_PLAIN_FIG_WIDTH,
        fig_height=PROPOSER_PRIORITY_PLAIN_FIG_HEIGHT
    )

    print_summary(blocks, stats, per_height, diffs)

    print()
    print("===== Output Files =====")
    print(presence_csv)
    print(per_height_csv)
    print(diff_summary_csv)
    print(diff_details_json)
    print(plot_validator_count_path)
    print(plot_validator_changes_path)
    print(plot_priority_changed_count_path)
    print(plot_all_validators_voting_power_scientific_path)
    print(plot_all_validators_voting_power_plain_path)
    print(plot_all_validators_proposer_priority_scientific_path)
    print(plot_all_validators_proposer_priority_plain_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())