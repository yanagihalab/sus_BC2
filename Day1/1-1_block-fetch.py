import os
import requests
import json
import time
import re
from tqdm import tqdm
from urllib.parse import urlparse

# 定数定義
# 使用する RPC エンドポイントを指定する
# 例:
# BASE_URL = "https://osmosis-rpc.publicnode.com:443"
# BASE_URL = "https://evmos-rpc.publicnode.com:443"
# BASE_URL = "https://juno-rpc.publicnode.com:443"
# BASE_URL = "https://terra-rpc.publicnode.com:443"

BASE_URL = "*__*"

BASE_URL_BLOCK = *__* + "/block"
BASE_URL_BLOCK_RESULTS = *__* + "/block_results"
BASE_URL_VALIDATORS = *__* + "/validators"

PER_PAGE = 100
TOTAL_PAGES = 1
RETRY_LIMIT = 100
SLEEP_TIME = 1
BLOCK_COUNT = *__*

parsed_base = urlparse(BASE_URL)
hostname = parsed_base.hostname or ""

m = re.match(r"^([a-zA-Z0-9\-]+)-rpc", hostname)
BASE_NAME = m.group(1) if m else hostname.split(".")[0]

SAVE_DIR = *__*

os.makedirs(SAVE_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}


def get_with_retry(url, timeout=10, retry_limit=RETRY_LIMIT, sleep_time=SLEEP_TIME):
    retries = 0

    while retries < retry_limit:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            retries += 1

            if retries >= retry_limit:
                raise e

            time.sleep(sleep_time)


def get_latest_height():
    latest_block = get_with_retry(BASE_URL_BLOCK, timeout=10)

    return int(
        latest_block["result"]["block"]["header"]["height"]
    )


latest_height = *__*

print(f"最新のブロック番号: {*__*}")
print(f"BASE_NAME: {*__*}")
print(f"保存先ディレクトリ: {*__*}")

for i in tqdm(range(BLOCK_COUNT), desc="Fetching blocks", unit="block"):
    height = latest_height - i

    block_header = {}
    block_last_commit = {}

    try:
        block_url = f"{BASE_URL_BLOCK}?height={height}"
        block_data = get_with_retry(block_url, timeout=10)

        block = (
            block_data.get("result", {})
            .get("block", {})
        )

        block_header = block.get("header", {})
        block_last_commit = block.get("last_commit", {})

    except requests.exceptions.RequestException as e:
        print(f"  Failed to fetch block header/last_commit for height {height}: {e}")

    block_results = {}

    try:
        block_results_url = f"{BASE_URL_BLOCK_RESULTS}?height={height}"
        block_results_data = get_with_retry(block_results_url, timeout=10)
        block_results = block_results_data.get("result", {})

    except requests.exceptions.RequestException as e:
        print(f"  Failed to fetch block results for height {height}: {e}")

    block_validators = []

    for page in range(1, TOTAL_PAGES + 1):
        url = f"{BASE_URL_VALIDATORS}?height={height}&per_page={PER_PAGE}&page={page}"
        retries = 0

        while retries < RETRY_LIMIT:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = *__*
                result = data.get("result")

                if not result or not isinstance(result, dict) or "validators" not in result:
                    break

                validators = result["validators"]

                if not validators:
                    break

                block_validators.extend(validators)
                break

            except requests.exceptions.RequestException:
                retries += 1
                time.sleep(SLEEP_TIME)

        if retries == RETRY_LIMIT:
            print(f"  Failed to fetch validator page {page} after {RETRY_LIMIT} attempts. Skipping.")

    if block_header or block_last_commit or block_results or block_validators:
        output = {
            "base_url": *__*,
            "blockheader": *__*,
            "last_commit": block_last_commit,
            "blockresults": *__*,
            "validators": *__*
        }

        filename = os.path.join(
            SAVE_DIR,
            f"{BASE_NAME}_BlockNum_{height}.json"
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)