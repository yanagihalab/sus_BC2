"""INJ 送金コマンドの応答と、起動から終了までの秒数を表示する。"""

import argparse
import math
import re
import subprocess
import sys
import time


# 設定：作成済みウォレットの鍵名・保存方式と、送金先・数量を指定する。
KEY_NAME = "testwallet"
KEYRING_BACKEND = "test"
CHAIN_ID = "injective-888"
NODE = "https://injective-testnet-rpc.publicnode.com:443"
GAS_PRICES = "500000000inj"
BANK_SEND_GAS = "200000"
AMOUNT = "1000000000000000inj"  # 0.001 INJ。
RECIPIENT_ADDR = ""  # 二重引用符の間に実際の受取アドレスを入力する。
CONFIRM_SEND = False  # 設定を確認し、送金する場合は True に変更する。


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=60, help="CLI timeout in seconds")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number.")

    for name, value, pattern in (
        ("RECIPIENT_ADDR", RECIPIENT_ADDR, r"inj1\S*"), ("AMOUNT", AMOUNT, r"[1-9][0-9]*inj"),
        ("BANK_SEND_GAS", BANK_SEND_GAS, r"[1-9][0-9]*"),
    ):
        if not re.fullmatch(pattern, str(value)):
            parser.error(f"Set {name} at the top of this file to a valid value.")
    if CONFIRM_SEND is not True:
        print("Set CONFIRM_SEND = True at the top of this file to measure one transfer.", file=sys.stderr)
        return 1

    command = [
        "injectived", "tx", "bank", "send",
        KEY_NAME, RECIPIENT_ADDR, AMOUNT,
        f"--from={KEY_NAME}", f"--keyring-backend={KEYRING_BACKEND}",
        f"--chain-id={CHAIN_ID}", f"--node={NODE}",
        f"--gas-prices={GAS_PRICES}", f"--gas={BANK_SEND_GAS}",
        "--broadcast-mode", "sync", "--output", "json", "-y",
    ]
    # CLI の応答（TxHash を含む）は、そのまま端末に表示する。
    start = time.perf_counter()
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, timeout=args.timeout, check=False).returncode
    except subprocess.TimeoutExpired:
        print("Timed out. Check the displayed response before another transfer.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. Check the displayed response before another transfer.", file=sys.stderr)
        return 130
    except OSError as error:
        print(f"Could not run injectived: {error}", file=sys.stderr)
        return 1
    finally:
        print(f"\nResponse time: {time.perf_counter() - start:.6f} seconds", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
