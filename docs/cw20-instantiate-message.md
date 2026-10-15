# CW20 初期化メッセージの作成

本書は、CW20 コントラクトの初期化に渡す JSON ファイルの作成方法を説明する。
CLI の設定とコントラクトへの操作は、[injectived の設定・操作手順](injective-setup.md) を参照する。
以下のコマンドは、リポジトリルートから実行する。

まずリポジトリへ移動し、`load-env.sh` で CW20 用の環境変数を現在の Bash に読み込む。表示された鍵名（`KEY_NAME`）と接続先（`CHAIN_ID`・`NODE`）を確認する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
```

同じ Bash で、トークン情報・初期残高・アドレス・出力ファイル名を環境変数に設定する。必要な値は空の二重引用符の間に入力する。空欄時の動作は各コメントを参照する。

各環境変数は、生成する JSON の項目またはファイルの保存先に次のように対応する。

| 環境変数 | JSON の項目・保存先 | 設定する内容 |
| --- | --- | --- |
| `TOKEN_NAME` | `name` | トークンの名称 |
| `TOKEN_SYMBOL` | `symbol` | トークンのシンボル |
| `TOKEN_DECIMALS` | `decimals` | 小数桁数 |
| `INITIAL_BALANCE` | `initial_balances[].amount` | 最小単位で指定する初期残高 |
| `CREATOR_ADDR` | `initial_balances[].address`・`mint.minter` | 初期残高の受取先と追加発行者のアドレス |
| `OUTPUT_FILE` | JSON ファイルの保存先 | 出力ファイル名またはパス |

`CREATOR_ADDR` が空欄の場合、`KEY_NAME` で指定した鍵と `KEYRING_BACKEND` で指定した保存方式を使ってアドレスを取得する。

```bash
# トークンの名称を入力する。空欄の場合は My Token を使う。
export TOKEN_NAME=""
# 英字またはハイフンの3〜12文字でシンボルを入力する。空欄の場合は MTK を使う。
export TOKEN_SYMBOL=""
# 小数桁数を数字で入力する。空欄の場合は 6 を使う。
export TOKEN_DECIMALS=""
# 初期残高を最小単位の数量で入力する。空欄の場合は 1000000 を使う。
export INITIAL_BALANCE=""
# 初期残高の受取先と追加発行者のアドレスを入力する。空欄の場合は現在の鍵から取得する。
export CREATOR_ADDR=""
# 出力ファイル名を入力する。空欄の場合は instantiate_msg.json を使う。
# ファイル名を変更した場合は、後続の jq や cat で使うファイル名も合わせる。
export OUTPUT_FILE=""
```

設定した環境変数を使い、初期化メッセージの JSON ファイルを生成する。スクリプトは生成後に `jq` で JSON の構文を確認し、内容を表示する。

```bash
bash ./scripts/CW20/create-instantiate-msg.sh
```

標準の出力ファイル名は `instantiate_msg.json` である。表示された JSON で、名称・シンボル・小数桁数・初期残高が設定どおりであること、`initial_balances` の受取先と `mint.minter` が意図したアドレスであることを確認する。
CW20 の symbol は英字またはハイフンの3〜12文字で指定する。TokenFactory の `factory/.../mtk` という denom は symbol として使用できない。

<details>
<summary>補足：初期化メッセージ生成スクリプトの内容</summary>

次は `create-instantiate-msg.sh` の主な内部処理である。設定値を既定値で補い、シンボルの形式を確認してから、初期残高と minter を含む JSON を書き出す。
`CREATOR_ADDR` が未設定または空欄の場合は、使用する鍵からアドレスを取得する。

```bash
# 設定した環境変数を使い、未設定または空欄の値を既定値で補う。
OUTPUT_FILE="${OUTPUT_FILE:-instantiate_msg.json}"
TOKEN_NAME="${TOKEN_NAME:-My Token}"
TOKEN_SYMBOL="${TOKEN_SYMBOL:-MTK}"
TOKEN_DECIMALS="${TOKEN_DECIMALS:-6}"
INITIAL_BALANCE="${INITIAL_BALANCE:-1000000}"
# シンボルが英字またはハイフンの3〜12文字であることを確認する。
if ! echo "$TOKEN_SYMBOL" | grep -Eq '^[A-Za-z-]{3,12}$'; then
  echo "Use only letters or hyphen, 3 to 12 characters." >&2
  exit 1
fi
# アドレスが未設定または空欄の場合は、使用中の鍵から取得する。
if [ -z "${CREATOR_ADDR:-}" ]; then
  CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
fi

# 設定値を使って初期化メッセージの JSON を書き出す。
cat > "$OUTPUT_FILE" <<EOF
{
  "name": "$TOKEN_NAME",
  "symbol": "$TOKEN_SYMBOL",
  "decimals": $TOKEN_DECIMALS,
  "initial_balances": [
    {
      "address": "$CREATOR_ADDR",
      "amount": "$INITIAL_BALANCE"
    }
  ],
  "mint": {
    "minter": "$CREATOR_ADDR"
  },
  "marketing": null
}
EOF
jq . "$OUTPUT_FILE"
```

`cat > ... <<EOF` は、`EOF` までの内容を変数展開してファイルに書き出す。
`initial_balances` は初期残高の宛先と最小単位の数量、`mint.minter` は追加発行できるアドレスを指定する。
`jq .` は生成した JSON の構文と内容を確認する。

</details>
