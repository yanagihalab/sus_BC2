import json
import os
import re
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

DATA_DIRECTORY = "current_osmosis"
MAX_BLOCKS = 5000
CSV_OUTPUT = "blockheader_blockresults_analysis.csv"
PLOT_DIR = "block_analysis_plots"

MAX_SIGNATURE_SPAN_SEC = 60


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


def parse_timestamp(ts: str):
    if not ts or ts == "N/A":
        return None

    try:
        ts = ts.replace("Z", "+00:00")

        if "." in ts:
            date_part, frac_part = ts.split(".", 1)

            if "+" in frac_part:
                frac, tz = frac_part.split("+", 1)
                frac = frac[:6]
                ts = f"{date_part}.{frac}+{tz}"
            elif "-" in frac_part:
                frac, tz = frac_part.split("-", 1)
                frac = frac[:6]
                ts = f"{date_part}.{frac}-{tz}"
            else:
                frac = frac_part[:6]
                ts = f"{date_part}.{frac}"

        return datetime.fromisoformat(ts)

    except Exception:
        return None


def extract_signature_timestamps(data):
    timestamps = []

    signatures = data.get("last_commit", {}).get("signatures", [])

    if not isinstance(signatures, list):
        return timestamps

    for sig in signatures:
        if not isinstance(sig, dict):
            continue

        block_id_flag = sig.get("block_id_flag")

        if block_id_flag not in (2, "2"):
            continue

        ts = sig.get("timestamp")
        parsed = parse_timestamp(ts)

        if parsed is None:
            continue

        if parsed.year < 2000:
            continue

        timestamps.append(parsed)

    return timestamps


def calculate_signature_time_span(data):
    sig_times = extract_signature_timestamps(data)

    if not sig_times:
        return {
            "signature_count": 0,
            "sig_min_time": None,
            "sig_max_time": None,
            "sig_time_span_sec": None,
        }

    sig_min = min(sig_times)
    sig_max = max(sig_times)
    sig_span = (sig_max - sig_min).total_seconds()

    if sig_span < 0:
        sig_span = None

    if sig_span is not None and sig_span > MAX_SIGNATURE_SPAN_SEC:
        sig_span = None

    return {
        "signature_count": len(sig_times),
        "sig_min_time": sig_min.isoformat(),
        "sig_max_time": sig_max.isoformat(),
        "sig_time_span_sec": sig_span,
    }


def analyze_block_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    blockheader = data.get("blockheader", {}) or {}
    blockresults = data.get("blockresults", {}) or {}

    filename = os.path.basename(file_path)

    txs_results = blockresults.get("txs_results") or []
    begin_block_events = blockresults.get("begin_block_events") or []
    end_block_events = blockresults.get("end_block_events") or []
    finalize_block_events = blockresults.get("finalize_block_events") or []

    sig_info = calculate_signature_time_span(data)

    result = {
        "file": filename,
        "height": safe_int(blockheader.get("height", extract_height_from_filename(filename))),
        "timestamp": blockheader.get("time", "N/A"),
        "chain_id": blockheader.get("chain_id", "N/A"),
        "proposer_address": blockheader.get("proposer_address", "N/A"),
        "num_transactions": len(txs_results),
        "num_begin_block_events": len(begin_block_events),
        "num_end_block_events": len(end_block_events),
        "num_finalize_block_events": len(finalize_block_events),
        "signature_count": sig_info["signature_count"],
        "sig_min_time": sig_info["sig_min_time"],
        "sig_max_time": sig_info["sig_max_time"],
        "sig_time_span_sec": sig_info["sig_time_span_sec"],
    }

    return result


def analyze_all_blocks(directory):
    results = []
    block_counter = 0

    filenames = sorted(
        os.listdir(directory),
        key=lambda x: extract_height_from_filename(x) or -1
    )

    for filename in filenames:
        if block_counter >= MAX_BLOCKS:
            print(f"{MAX_BLOCKS}ブロックに到達しました。処理を終了します。")
            break

        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(directory, filename)

        try:
            analysis = analyze_block_json(file_path)
            results.append(analysis)
            block_counter += 1
        except Exception as e:
            print(f"Failed to analyze {filename}: {e}")

    return results


def add_block_diff_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["parsed_timestamp"] = df["timestamp"].apply(parse_timestamp)

    block_diffs = [None]

    for i in range(1, len(df)):
        prev_ts = df.loc[i - 1, "parsed_timestamp"]
        curr_ts = df.loc[i, "parsed_timestamp"]

        if prev_ts is None or curr_ts is None:
            block_diffs.append(None)
        else:
            diff_sec = (curr_ts - prev_ts).total_seconds()
            block_diffs.append(diff_sec)

    df["block_diff_sec"] = block_diffs
    return df


def make_transactions_per_block_line(df: pd.DataFrame, plot_dir: str):
    os.makedirs(plot_dir, exist_ok=True)

    if df.empty:
        print("DataFrame が空のため、transactions_per_block_line を作成できません。")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df["height"], df["num_transactions"], marker="o", markersize=3, linewidth=1)
    plt.xlabel("Height")
    plt.ylabel("Number of Transactions")
    plt.title("Transactions per Block")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(plot_dir, "transactions_per_block_line.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"保存しました: {output_path}")


def make_transaction_histogram(df: pd.DataFrame, plot_dir: str):
    os.makedirs(plot_dir, exist_ok=True)

    if df.empty:
        print("DataFrame が空のため、transactions_per_block_histogram を作成できません。")
        return

    plt.figure(figsize=(12, 6))
    plt.hist(df["num_transactions"], bins=50)
    plt.xlabel("Number of Transactions per Block")
    plt.ylabel("Frequency")
    plt.title("Histogram of Transactions per Block")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(plot_dir, "transactions_per_block_histogram.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"保存しました: {output_path}")


def make_block_diff_line(df: pd.DataFrame, plot_dir: str):
    os.makedirs(plot_dir, exist_ok=True)

    valid_df = df.dropna(subset=["block_diff_sec"])

    if valid_df.empty:
        print("block_diff_sec が空のため、block_diff_line を作成できません。")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(valid_df["height"], valid_df["block_diff_sec"], marker="o", markersize=3, linewidth=1)
    plt.xlabel("Height")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Block Time Difference over Height")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(plot_dir, "block_diff_line.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"保存しました: {output_path}")


def make_block_diff_histogram(df: pd.DataFrame, plot_dir: str):
    os.makedirs(plot_dir, exist_ok=True)

    valid_diffs = df["block_diff_sec"].dropna()

    if valid_diffs.empty:
        print("block_diff_sec が空のため、block_diff_histogram を作成できません。")
        return

    plt.figure(figsize=(12, 6))
    plt.hist(valid_diffs, bins=50)
    plt.xlabel("Block Time Difference (seconds)")
    plt.ylabel("Frequency")
    plt.title("Histogram of Block Time Differences")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(plot_dir, "block_diff_histogram.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"保存しました: {output_path}")


def make_signature_time_span_histogram(df: pd.DataFrame, plot_dir: str):
    os.makedirs(plot_dir, exist_ok=True)

    valid_spans = df["sig_time_span_sec"].dropna()

    if valid_spans.empty:
        print("sig_time_span_sec が空のため、validator署名時間差ヒストグラムを作成できません。")
        print("JSONに last_commit.signatures[].timestamp が保存されているか確認してください。")
        return

    plt.figure(figsize=(12, 6))
    plt.hist(valid_spans, bins=50)
    plt.xlabel("Validator Signature Time Span per Block (seconds)")
    plt.ylabel("Frequency")
    plt.title("Histogram of Validator Signature Time Span")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(plot_dir, "validator_signature_time_span_histogram.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"保存しました: {output_path}")


def print_transaction_count_summary(df: pd.DataFrame):
    print("\nTransaction count summary:")
    print(f"  Blocks analyzed : {len(df)}")
    print(f"  Min tx/block    : {df['num_transactions'].min()}")
    print(f"  Max tx/block    : {df['num_transactions'].max()}")
    print(f"  Mean tx/block   : {df['num_transactions'].mean():.6f}")
    print(f"  Median tx/block : {df['num_transactions'].median():.6f}")
    print(f"  P90 tx/block    : {df['num_transactions'].quantile(0.90):.6f}")
    print(f"  P99 tx/block    : {df['num_transactions'].quantile(0.99):.6f}")


def print_block_diff_summary(df: pd.DataFrame):
    valid_diffs = df["block_diff_sec"].dropna()

    print("\nBlock time difference summary:")
    if valid_diffs.empty:
        print("  No valid block_diff_sec data.")
        return

    print(f"  Count  : {len(valid_diffs)}")
    print(f"  Min    : {valid_diffs.min():.6f} sec")
    print(f"  Max    : {valid_diffs.max():.6f} sec")
    print(f"  Mean   : {valid_diffs.mean():.6f} sec")
    print(f"  Median : {valid_diffs.median():.6f} sec")
    print(f"  P90    : {valid_diffs.quantile(0.90):.6f} sec")
    print(f"  P99    : {valid_diffs.quantile(0.99):.6f} sec")


def print_signature_time_span_summary(df: pd.DataFrame):
    valid_spans = df["sig_time_span_sec"].dropna()

    print("\nValidator signature time span summary:")
    if valid_spans.empty:
        print("  No valid sig_time_span_sec data.")
        return

    print(f"  Count  : {len(valid_spans)}")
    print(f"  Min    : {valid_spans.min():.6f} sec")
    print(f"  Max    : {valid_spans.max():.6f} sec")
    print(f"  Mean   : {valid_spans.mean():.6f} sec")
    print(f"  Median : {valid_spans.median():.6f} sec")
    print(f"  P90    : {valid_spans.quantile(0.90):.6f} sec")
    print(f"  P99    : {valid_spans.quantile(0.99):.6f} sec")


if __name__ == "__main__":
    all_results = analyze_all_blocks(DATA_DIRECTORY)

    if not all_results:
        print("分析対象データがありません。")
        raise SystemExit(1)

    df = pd.DataFrame(all_results)
    df = df.sort_values("height").reset_index(drop=True)

    df = add_block_diff_columns(df)

    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"CSVファイル '{CSV_OUTPUT}' に保存しました。")

    make_transactions_per_block_line(df, PLOT_DIR)
    make_transaction_histogram(df, PLOT_DIR)
    make_block_diff_line(df, PLOT_DIR)
    make_block_diff_histogram(df, PLOT_DIR)
    make_signature_time_span_histogram(df, PLOT_DIR)

    print_transaction_count_summary(df)
    print_block_diff_summary(df)
    print_signature_time_span_summary(df)