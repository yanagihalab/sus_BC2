# CW20 初期化メッセージの作成

本書は、CW20 コントラクトの初期化に渡す JSON ファイルの作成方法を説明する。
CLI の設定とコントラクトへの操作は、[injectived の設定・操作手順](injective-setup.md) を参照する。
以下のコマンドは、リポジトリルートから実行する。

初期化メッセージ（instantiate message）は、次のシェルスクリプトで作成する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
```

同じ Bash で、必要な値を空の二重引用符の間に入力して設定する。空欄の場合は、各コメントに記載した既定値を使う。

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

設定後、次のコマンドで JSON ファイルを作成する。

```bash
bash ./scripts/CW20/create-instantiate-msg.sh
```

標準の出力ファイル名は `instantiate_msg.json` で、生成後に JSON の内容を表示する。
CW20 の symbol は英字またはハイフンの3〜12文字で指定する。TokenFactory の `factory/.../mtk` という denom は symbol として使用できない。

<details>
<summary>補足：初期化メッセージ生成スクリプトの内容</summary>

`create-instantiate-msg.sh` は、次の値を使って初期残高と minter を含む JSON を作成する。
`CREATOR_ADDR` が未設定の場合は、鍵からアドレスを取得する。

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
