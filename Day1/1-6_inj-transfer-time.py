"""INJ 送金コマンドの応答と、起動から終了までの秒数を表示する。"""

import argparse
import math
import os
import re
import subprocess
import sys
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=60, help="CLI timeout in seconds")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number.")

    # 既存の手順で設定した環境変数を使う。
    defaults = {
        "KEY_NAME": "testwallet", "KEYRING_BACKEND": "test",
        "CHAIN_ID": "injective-888", "NODE": "https://injective-testnet-rpc.publicnode.com:443",
        "GAS_PRICES": "500000000inj", "BANK_SEND_GAS": "200000",
        "AMOUNT": "1000000000000000inj", "RECIPIENT_ADDR": "",
    }
    settings = {name: os.environ.get(name) or default for name, default in defaults.items()}
    for name, pattern in (
        ("RECIPIENT_ADDR", r"inj1\S*"), ("AMOUNT", r"[1-9][0-9]*inj"),
        ("BANK_SEND_GAS", r"[1-9][0-9]*"),
    ):
        if not re.fullmatch(pattern, settings[name]):
            parser.error(f"Set {name} to a valid value.")
    if os.environ.get("CONFIRM_SEND") != "yes":
        print("Run with CONFIRM_SEND=yes to measure one transfer.", file=sys.stderr)
        return 1

    command = [
        "injectived", "tx", "bank", "send",
        settings["KEY_NAME"], settings["RECIPIENT_ADDR"], settings["AMOUNT"],
        f'--from={settings["KEY_NAME"]}', f'--keyring-backend={settings["KEYRING_BACKEND"]}',
        f'--chain-id={settings["CHAIN_ID"]}', f'--node={settings["NODE"]}',
        f'--gas-prices={settings["GAS_PRICES"]}', f'--gas={settings["BANK_SEND_GAS"]}',
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
