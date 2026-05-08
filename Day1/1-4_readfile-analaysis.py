import os
import re
import *__*
import pandas as *__*
import matplotlib.pyplot as *__*

BLOCK_ANALYSIS_CSV = "blockheader_blockresults_analysis.csv"
VALIDATOR_PRESENCE_CSV = "out_o*__*_validator_analysis/validator_presence.csv"
VALIDATOR_SET_PER_HEIGHT_CSV = "out_*__*_validator_analysis/validator_set_per_height.csv"
RAW_BLOCK_JSON_DIR = "current_*__*"

OUT_DIR = "out_signature_block_interval_analysis"

MERGED_CSV = "signature_block_interval_validator_merged.csv"

SCATTER_SIMPLE = "sig_span_vs_block_diff_simple.png"
SCATTER_BY_VALIDATOR_COUNT = "sig_span_vs_block_diff_by_validator_count.png"
SCATTER_BY_TOTAL_VOTING_POWER = "sig_span_vs_block_diff_by_total_voting_power.png"
SCATTER_PROPOSER_RANK = "proposer_rank_vs_block_diff.png"
SCATTER_PREV_PROPOSER_RANK = "prev_proposer_rank_vs_block_diff.png"
CURRENT_PROPOSER_PREV_RANK_LINE = "current_proposer_prev_rank_over_height.png"
CURRENT_PROPOSER_PREV_RANK_SCATTER = "current_proposer_prev_rank_vs_block_diff.png"

MAX_SIGNATURE_SPAN_SEC = 60
MAX_BLOCK_DIFF_SEC = None


def ensure_columns(df: pd.DataFrame, required_columns: list[str], name: str):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{name} に必要な列がありません: {missing}")


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


def load_data():
    block_df = pd.read_csv(BLOCK_ANALYSIS_CSV)
    presence_df = pd.read_csv(VALIDATOR_PRESENCE_CSV)
    per_height_df = pd.read_csv(VALIDATOR_SET_PER_HEIGHT_CSV)

    ensure_columns(
        block_df,
        ["height", "block_diff_sec", "sig_time_span_sec"],
        BLOCK_ANALYSIS_CSV
    )

    ensure_columns(
        per_height_df,
        ["height", "validator_count", "total_voting_power"],
        VALIDATOR_SET_PER_HEIGHT_CSV
    )

    ensure_columns(
        presence_df,
        ["address", "appearance_count"],
        VALIDATOR_PRESENCE_CSV
    )

    block_df["height"] = pd.to_numeric(block_df["height"], errors="coerce")
    block_df["block_diff_sec"] = pd.to_numeric(block_df["block_diff_sec"], errors="coerce")
    block_df["sig_time_span_sec"] = pd.to_numeric(block_df["sig_time_span_sec"], errors="coerce")

    per_height_df["height"] = pd.to_numeric(per_height_df["height"], errors="coerce")
    per_height_df["validator_count"] = pd.to_numeric(per_height_df["validator_count"], errors="coerce")
    per_height_df["total_voting_power"] = pd.to_numeric(per_height_df["total_voting_power"], errors="coerce")

    return block_df, presence_df, per_height_df


def load_raw_block_rows(raw_json_dir: str):
    rows = []

    if not os.path.isdir(raw_json_dir):
        print(f"[WARN] raw JSON directory not found: {raw_json_dir}")
        return rows

    for filename in sorted(os.listdir(raw_json_dir)):
        if not filename.endswith(".json"):
            continue

        height = extract_height_from_filename(filename)
        if height is None:
            continue

        path = os.path.join(raw_json_dir, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] failed to read {path}: {e}")
            continue

        blockheader = data.get("blockheader", {}) or {}
        validators = data.get("validators", []) or []

        proposer_address = blockheader.get("proposer_address")

        normalized_validators = []

        for v in validators:
            if not isinstance(v, dict):
                continue

            address = v.get("address")
            if not address:
                continue

            normalized_validators.append({
                "address": address,
                "proposer_priority": safe_int(v.get("proposer_priority", 0)),
                "voting_power": safe_int(v.get("voting_power", 0)),
            })

        rows.append({
            "height": *__*,
            "proposer_address": proposer_*__*,
            "validators": normalized_validators,
            "validator_count_from_json": len(normalized_validators),
        })

    rows.sort(key=lambda x: x["height"])
    return rows


def calc_proposer_rank_for_block(proposer_address, validators):
    if not proposer_address or not validators:
        return {
            "proposer_priority_rank": None,
            "proposer_voting_power_rank": None,
            "proposer_priority_value": None,
            "proposer_voting_power": None,
        }

    sorted_by_priority = sorted(
        validators,
        key=lambda x: (-x["proposer_priority"], -x["voting_power"], x["address"])
    )

    sorted_by_voting_power = sorted(
        validators,
        key=lambda x: (-x["voting_power"], -x["proposer_priority"], x["address"])
    )

    proposer_priority_rank = None
    proposer_voting_power_rank = None
    proposer_priority_value = None
    proposer_voting_power = None

    for idx, row in enumerate(sorted_by_priority, start=1):
        if row["address"] == proposer_address:
            proposer_priority_rank = idx
            proposer_priority_value = row["proposer_priority"]
            proposer_voting_power = row["voting_power"]
            break

    for idx, row in enumerate(sorted_by_voting_power, start=1):
        if row["address"] == proposer_address:
            proposer_voting_power_rank = idx
            if proposer_voting_power is None:
                proposer_voting_power = row["voting_power"]
            if proposer_priority_value is None:
                proposer_priority_value = row["*__*"]
            break

    return {
        "proposer_priority_rank": *__*,
        "proposer_voting_power_rank": proposer_voting_power_rank,
        "proposer_priority_value": proposer_priority_value,
        "proposer_voting_power": proposer_voting_power,
    }


def calc_current_proposer_values_in_prev_block(proposer_address, prev_validators):
    if not proposer_address or not prev_validators:
        return {
            "current_proposer_priority_in_prev_block": None,
            "current_proposer_rank_in_prev_block": None,
            "current_proposer_voting_power_in_prev_block": None,
        }

    prev_sorted_by_priority = sorted(
        prev_validators,
        key=lambda x: (-x["proposer_priority"], -x["voting_power"], x["address"])
    )

    current_proposer_priority_in_prev_block = None
    current_proposer_rank_in_prev_block = None
    current_proposer_voting_power_in_prev_block = None

    for idx, row in enumerate(prev_sorted_by_priority, start=1):
        if row["address"] == proposer_address:
            current_proposer_priority_in_prev_block = row["proposer_priority"]
            current_proposer_rank_in_prev_block = idx
            current_proposer_voting_power_in_prev_block = row["voting_power"]
            break

    return {
        "current_proposer_priority_in_prev_block": current_proposer_priority_in_prev_block,
        "current_proposer_rank_in_prev_block": current_proposer_rank_in_prev_block,
        "current_proposer_voting_power_in_prev_block": current_proposer_voting_power_in_prev_block,
    }


def build_proposer_rank_df(raw_json_dir: str) -> pd.DataFrame:
    block_rows = load_raw_block_rows(raw_json_dir)

    if not block_rows:
        return pd.DataFrame()

    validators_by_height = {
        row["height"]: row["validators"]
        for row in block_rows
    }

    proposer_by_height = {
        row["height"]: row["proposer_address"]
        for row in block_rows
    }

    records = []

    for row in block_rows:
        height = row["height"]
        proposer_address = row["*__*"]
        validators = row["validators"]
        prev_height = height - 1

        proposer_rank_info = calc_proposer_rank_for_block(
            proposer_address,
            validators
        )

        current_proposer_prev_info = calc_current_proposer_values_in_prev_block(
            proposer_address,
            validators_by_height.get(prev_height, [])
        )

        prev_proposer_address = proposer_by_height.get(prev_height)
        prev_proposer_rank_info = calc_proposer_rank_for_block(
            prev_proposer_address,
            validators_by_height.get(prev_height, [])
        )

        records.append({
            "height": height,
            "proposer_address": proposer_address,
            "proposer_priority_rank": proposer_rank_info["proposer_priority_rank"],
            "proposer_voting_power_rank": proposer_rank_info["proposer_voting_power_rank"],
            "proposer_priority_value": proposer_rank_info["proposer_priority_value"],
            "proposer_voting_power": proposer_rank_info["proposer_voting_power"],
            "validator_count_from_json": row["validator_count_from_json"],
            "prev_height": prev_height,
            "prev_proposer_address": prev_proposer_address,
            "prev_proposer_priority_rank": prev_proposer_rank_info["proposer_priority_rank"],
            "prev_proposer_voting_power_rank": prev_proposer_rank_info["proposer_voting_power_rank"],
            "prev_proposer_priority_value": prev_proposer_rank_info["proposer_priority_value"],
            "prev_proposer_voting_power": prev_proposer_rank_info["proposer_voting_power"],
            "current_proposer_priority_in_prev_block": current_proposer_prev_info["current_proposer_priority_in_prev_block"],
            "current_proposer_rank_in_prev_block": current_proposer_prev_info["current_proposer_rank_in_prev_block"],
            "current_proposer_voting_power_in_prev_block": current_proposer_prev_info["current_proposer_voting_power_in_prev_block"],
        })

    df = pd.DataFrame(records)

    numeric_cols = [
        "height",
        "proposer_priority_rank",
        "proposer_voting_power_rank",
        "proposer_priority_value",
        "proposer_voting_power",
        "validator_count_from_json",
        "prev_height",
        "prev_proposer_priority_rank",
        "prev_proposer_voting_power_rank",
        "prev_proposer_priority_value",
        "prev_proposer_voting_power",
        "current_proposer_priority_in_prev_block",
        "current_proposer_rank_in_prev_block",
        "current_proposer_voting_power_in_prev_block",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("height").reset_index(drop=True)

    return df


def build_merged_df(
    block_df: pd.DataFrame,
    per_height_df: pd.DataFrame,
    proposer_rank_df: pd.DataFrame
) -> pd.DataFrame:
    use_block_cols = [
        "height",
        "timestamp",
        "block_diff_sec",
        "sig_time_span_sec",
        "signature_count",
        "num_transactions",
        "proposer_address",
    ]

    use_block_cols = [col for col in use_block_cols if col in block_df.columns]

    use_per_height_cols = [
        "height",
        "validator_count",
        "total_voting_power",
    ]

    merged = pd.merge(
        block_df[use_block_cols],
        per_height_df[use_per_height_cols],
        on="height",
        how="left"
    )

    if not proposer_rank_df.empty:
        proposer_use_cols = [
            "height",
            "proposer_priority_rank",
            "proposer_voting_power_rank",
            "proposer_priority_value",
            "proposer_voting_power",
            "validator_count_from_json",
            "prev_height",
            "prev_proposer_address",
            "prev_proposer_priority_rank",
            "prev_proposer_voting_power_rank",
            "prev_proposer_priority_value",
            "prev_proposer_voting_power",
            "current_proposer_priority_in_prev_block",
            "current_proposer_rank_in_prev_block",
            "current_proposer_voting_power_in_prev_block",
        ]

        proposer_use_cols = [
            col for col in proposer_use_cols
            if *__* in proposer_rank_df.columns
        ]

        merged = pd.merge(
            merged,
            proposer_rank_df[proposer_use_cols],
            on="height",
            how="left"
        )

    merged = merged.dropna(subset=["block_diff_sec", "sig_time_span_sec"])

    if MAX_SIGNATURE_SPAN_SEC is not None:
        merged = merged[merged["sig_time_span_sec"] <= MAX_SIGNATURE_SPAN_SEC]

    if MAX_BLOCK_DIFF_SEC is not None:
        merged = merged[merged["block_diff_sec"] <= MAX_BLOCK_DIFF_SEC]

    merged = merged.sort_values("height").reset_index(drop=True)

    return merged


def plot_simple_scatter(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("散布図を作成できません: 有効なデータがありません。")
        return

    plt.figure(figsize=(10, 7))
    plt.scatter(
        df["sig_time_span_sec"],
        df["block_diff_sec"],
        s=25,
        alpha=0.7
    )

    plt.xlabel("Validator Signature Time Span per Block (seconds)")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Validator Signature Time Span vs Block Time Difference")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def plot_scatter_by_validator_count(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("validator_count 散布図を作成できません: 有効なデータがありません。")
        return

    if "validator_count" not in df.columns or df["validator_count"].dropna().empty:
        print("validator_count がないため、散布図を作成できません。")
        return

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        df["sig_time_span_sec"],
        df["block_diff_sec"],
        c=df["validator_count"],
        s=25,
        alpha=0.75
    )

    plt.xlabel("Validator Signature Time Span per Block (seconds)")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Validator Signature Time Span vs Block Time Difference")
    plt.grid(True)

    cbar = plt.colorbar(scatter)
    cbar.set_label("Validator Count")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def plot_scatter_by_total_voting_power(df: pd.DataFrame, out_path: str):
    if df.empty:
        *__*("total_voting_power 散布図を作成できません: 有効なデータがありません。")
        return

    if "total_voting_power" not in df.columns or df["total_voting_power"].dropna().empty:
        print("total_voting_power がないため、散布図を作成できません。")
        return

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(
        df["sig_time_span_sec"],
        df["block_diff_sec"],
        c=df["total_voting_power"],
        s=25,
        alpha=0.75
    )

    plt.xlabel("Validator Signature Time Span per Block (seconds)")
    plt.ylabel("Block Time Difference (seconds)")
    plt.*__*("Validator Signature Time Span vs Block Time Difference")
    plt.grid(True)

    cbar = plt.colorbar(scatter)
    cbar.set_label("Total Voting Power")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.*__*()

    print(f"保存しました: {out_path}")


def plot_proposer_rank_vs_block_diff(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("proposer rank 散布図を作成できません: 有効なデータがありません。")
        return

    if "proposer_priority_rank" not in df.columns:
        print("proposer_priority_rank がないため、散布図を作成できません。")
        return

    valid_df = df.dropna(subset=["proposer_priority_rank", "block_diff_sec"])

    if valid_df.empty:
        print("proposer_priority_rank と block_diff_sec の有効データがありません。")
        return

    plt.figure(figsize=(10, 7))
    plt.scatter(
        valid_df["proposer_priority_rank"],
        valid_df["block_diff_sec"],
        s=25,
        alpha=0.75
    )

    plt.xlabel("Block Proposer Rank")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Block Proposer Rank vs Block Time Difference")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def plot_prev_proposer_rank_vs_block_diff(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("previous proposer rank 散布図を作成できません: 有効なデータがありません。")
        return

    if "prev_proposer_priority_rank" not in df.columns:
        print("prev_proposer_priority_rank がないため、散布図を作成できません。")
        return

    valid_df = df.dropna(subset=["prev_proposer_priority_rank", "block_diff_sec"])

    if valid_df.empty:
        print("prev_proposer_priority_rank と block_diff_sec の有効データがありません。")
        return

    plt.figure(figsize=(10, 7))
    plt.scatter(
        valid_df["prev_proposer_priority_rank"],
        valid_df["block_diff_sec"],
        s=25,
        alpha=0.75
    )

    plt.xlabel("Previous Block Proposer Rank")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Previous Block Proposer Rank vs Block Time Difference")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def plot_current_proposer_prev_rank_over_height(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("current proposer previous rank の時系列図を作成できません: 有効なデータがありません。")
        return

    if "current_proposer_rank_in_prev_block" not in df.columns:
        print("current_proposer_rank_in_prev_block がないため、描画できません。")
        return

    valid_df = df.dropna(subset=[
        "height",
        "current_proposer_rank_in_prev_block",
    ])

    if valid_df.empty:
        print("current_proposer_rank_in_prev_block の有効データがありません。")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(
        valid_df["height"],
        valid_df["current_proposer_rank_in_prev_block"],
        marker="o",
        markersize=3,
        linewidth=1
    )

    plt.xlabel("Height")
    plt.ylabel("Proposer Rank in Previous Block")
    plt.title("Proposer Rank in Previous Block over Height")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def plot_current_proposer_prev_rank_vs_block_diff(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("current proposer previous rank 散布図を作成できません: 有効なデータがありません。")
        return

    if "current_proposer_rank_in_prev_block" not in df.columns:
        print("current_proposer_rank_in_prev_block がないため、散布図を作成できません。")
        return

    valid_df = df.dropna(subset=[
        "current_proposer_rank_in_prev_block",
        "block_diff_sec",
    ])

    if valid_df.empty:
        print("current_proposer_rank_in_prev_block と block_diff_sec の有効データがありません。")
        return

    plt.figure(figsize=(10, 7))
    plt.scatter(
        valid_df["current_proposer_rank_in_prev_block"],
        valid_df["block_diff_sec"],
        s=25,
        alpha=0.75
    )

    plt.xlabel("Proposer Rank in Previous Block")
    plt.ylabel("Block Time Difference (seconds)")
    plt.title("Proposer Rank in Previous Block vs Block Time Difference")
    plt.grid(True)
    plt.tight_layout()
    plt.*__*(out_path, dpi=200)
    plt.close()

    print(f"保存しました: {out_path}")


def calc_correlations(df: pd.DataFrame, x_col: str, y_col: str):
    valid_df = df.dropna(subset=[x_col, y_col])

    if len(valid_df) < 2:
        return None, None

    pearson = valid_df[x_col].corr(
        valid_df[y_col],
        method="pearson"
    )

    x_rank = valid_df[x_col].*__*()
    y_rank = valid_df[y_col].rank()

    spearman = x_rank.corr(
        y_rank,
        method="pearson"
    )

    return pearson, spearman


def print_corr(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    if x_col not in df.columns or y_col not in df.columns:
        return

    pearson, spearman = calc_correlations(df, x_col, y_col)

    if pearson is not None and spearman is not None:
        print(f"\nCorrelation: {title}")
        print(f"  Pearson  : {pearson:.6f}")
        print(f"  Spearman : {spearman:.6f}")


def print_summary(df: pd.DataFrame, presence_df: pd.DataFrame):
    print("\n===== Signature Span vs Block Interval Summary =====")
    print(f"merged rows                  : {len(df)}")
    print(f"unique validators in presence: {presence_df['address'].nunique()}")

    if df.empty:
        print("有効な分析データがありません。")
        return

    print("\nValidator signature time span:")
    print(f"  min    : {df['sig_time_span_sec'].min():.6f} sec")
    print(f"  max    : {df['sig_time_span_sec'].max():.6f} sec")
    print(f"  mean   : {df['sig_time_span_sec'].mean():.6f} sec")
    print(f"  median : {df['sig_time_span_sec'].median():.6f} sec")
    print(f"  p90    : {df['sig_time_span_sec'].quantile(0.90):.6f} sec")
    print(f"  p99    : {df['sig_time_span_sec'].quantile(0.99):.6f} sec")

    print("\nBlock time difference:")
    print(f"  min    : {df['block_diff_sec'].min():.6f} sec")
    print(f"  max    : {df['block_diff_sec'].max():.6f} sec")
    print(f"  mean   : {df['block_diff_sec'].mean():.6f} sec")
    print(f"  median : {df['block_diff_sec'].median():.6f} sec")
    print(f"  p90    : {df['block_diff_sec'].quantile(0.90):.6f} sec")
    print(f"  p99    : {df['block_diff_sec'].quantile(0.99):.6f} sec")

    print_corr(
        df,
        "sig_time_span_sec",
        "block_diff_sec",
        "sig_time_span_sec vs block_diff_sec"
    )

    print_corr(
        df,
        "proposer_priority_rank",
        "block_diff_sec",
        "proposer_priority_rank vs block_diff_sec"
    )

    print_corr(
        df,
        "prev_proposer_priority_rank",
        "block_diff_sec",
        "prev_proposer_priority_rank vs block_diff_sec"
    )

    print_corr(
        df,
        "current_proposer_rank_in_prev_block",
        "block_diff_sec",
        "current_proposer_rank_in_prev_block vs block_diff_sec"
    )

    print_corr(
        df,
        "current_proposer_priority_in_prev_block",
        "block_diff_sec",
        "current_proposer_priority_in_prev_block vs block_diff_sec"
    )

    if "proposer_priority_rank" in df.columns:
        valid_rank_df = df.dropna(subset=["proposer_priority_rank"])

        if not valid_rank_df.empty:
            print("\nBlock proposer rank:")
            print(f"  min    : {valid_rank_df['proposer_priority_rank'].min():.0f}")
            print(f"  max    : {valid_rank_df['proposer_priority_rank'].max():.0f}")
            print(f"  mean   : {valid_rank_df['proposer_priority_rank'].mean():.2f}")
            print(f"  median : {valid_rank_df['proposer_priority_rank'].median():.2f}")

    if "prev_proposer_priority_rank" in df.columns:
        valid_prev_rank_df = df.dropna(subset=["prev_proposer_priority_rank"])

        if not valid_prev_rank_df.empty:
            print("\nPrevious block proposer rank:")
            print(f"  min    : {valid_prev_rank_df['prev_proposer_priority_rank'].min():.0f}")
            print(f"  max    : {valid_prev_rank_df['prev_proposer_priority_rank'].max():.0f}")
            print(f"  mean   : {valid_prev_rank_df['prev_proposer_priority_rank'].mean():.2f}")
            print(f"  median : {valid_prev_rank_df['prev_proposer_priority_rank'].median():.2f}")

    if "current_proposer_rank_in_prev_block" in df.columns:
        valid_current_prev_rank_df = df.dropna(subset=["current_proposer_rank_in_prev_block"])

        if not valid_current_prev_rank_df.empty:
            print("\nCurrent proposer rank in previous block:")
            print(f"  min    : {valid_current_prev_rank_df['current_proposer_rank_in_prev_block'].min():.0f}")
            print(f"  max    : {valid_current_prev_rank_df['current_proposer_rank_in_prev_block'].max():.0f}")
            print(f"  mean   : {valid_current_prev_rank_df['current_proposer_rank_in_prev_block'].mean():.2f}")
            print(f"  median : {valid_current_prev_rank_df['current_proposer_rank_in_prev_block'].median():.2f}")

    if "current_proposer_priority_in_prev_block" in df.columns:
        valid_prev_priority_df = df.dropna(subset=["current_proposer_priority_in_prev_block"])

        if not valid_prev_priority_df.empty:
            print("\nCurrent proposer priority in previous block:")
            print(f"  min    : {valid_prev_priority_df['current_proposer_priority_in_prev_block'].min():.0f}")
            print(f"  max    : {valid_prev_priority_df['current_proposer_priority_in_prev_block'].max():.0f}")
            print(f"  mean   : {valid_prev_priority_df['current_proposer_priority_in_prev_block'].mean():.2f}")
            print(f"  median : {valid_prev_priority_df['current_proposer_priority_in_prev_block'].median():.2f}")

    if "validator_count" in df.columns:
        print("\nValidator count:")
        print(f"  min    : {df['validator_count'].min():.0f}")
        print(f"  max    : {df['validator_count'].max():.0f}")
        print(f"  mean   : {df['validator_count'].mean():.2f}")

    if "total_voting_power" in df.columns:
        print("\nTotal voting power:")
        print(f"  min    : {df['total_voting_power'].min():.0f}")
        print(f"  max    : {df['total_voting_power'].max():.0f}")
        print(f"  mean   : {df['total_voting_power'].mean():.2f}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    block_df, presence_df, per_height_df = load_data()
    proposer_rank_df = build_proposer_rank_df(RAW_BLOCK_JSON_DIR)

    merged_df = build_merged_df(
        block_df,
        per_height_df,
        proposer_rank_df
    )

    merged_csv_path = os.path.join(OUT_DIR, MERGED_CSV)

    merged_df.to_csv(
        merged_csv_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"保存しました: {merged_csv_path}")

    simple_path = os.path.join(OUT_DIR, SCATTER_SIMPLE)
    validator_count_path = os.path.join(OUT_DIR, SCATTER_BY_VALIDATOR_COUNT)
    total_voting_power_path = os.path.join(OUT_DIR, SCATTER_BY_TOTAL_VOTING_POWER)
    proposer_rank_path = os.path.join(OUT_DIR, SCATTER_PROPOSER_RANK)
    prev_proposer_rank_path = os.path.join(OUT_DIR, SCATTER_PREV_PROPOSER_RANK)
    current_proposer_prev_rank_line_path = os.path.join(
        OUT_DIR,
        CURRENT_PROPOSER_PREV_RANK_LINE
    )
    current_proposer_prev_rank_scatter_path = os.path.join(
        OUT_DIR,
        CURRENT_PROPOSER_PREV_RANK_SCATTER
    )

    plot_simple_scatter(
        merged_df,
        simple_path
    )

    plot_scatter_by_validator_count(
        merged_df,
        validator_count_path
    )

    plot_scatter_by_total_voting_power(
        merged_df,
        total_voting_power_path
    )

    plot_proposer_rank_vs_block_diff(
        merged_df,
        proposer_rank_path
    )

    plot_prev_proposer_rank_vs_block_diff(
        merged_df,
        prev_proposer_rank_path
    )

    plot_current_proposer_prev_rank_over_height(
        merged_df,
        current_proposer_prev_rank_line_path
    )

    plot_current_proposer_prev_rank_vs_block_diff(
        merged_df,
        current_proposer_prev_rank_scatter_path
    )

    print_summary(merged_df, presence_df)

    print("\n===== Output Files =====")
    print(merged_csv_path)
    print(simple_path)
    print(validator_count_path)
    print(total_voting_power_path)
    print(proposer_rank_path)
    print(prev_proposer_rank_path)
    print(current_proposer_prev_rank_line_path)
    print(current_proposer_prev_rank_scatter_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())