# CW20 初期化メッセージの作成

本書は、CW20 コントラクトの初期化に渡す JSON ファイルの作成方法を説明する。
CLI の設定とコントラクトへの操作は、[injectived の設定・操作手順](injective-setup.md) を参照する。
以下のコマンドは、リポジトリルートから実行する。

初期化メッセージ（instantiate message）は、次のシェルスクリプトで作成する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
scripts/CW20/create-instantiate-msg.sh
```

このスクリプトは `instantiate_msg.json` を生成する。
CW20 の symbol は英字またはハイフンの3〜12文字で指定する。TokenFactory の `factory/.../mtk` という denom は symbol として使用できない。

<details>
<summary>補足：初期化メッセージ生成スクリプトの内容</summary>

`create-instantiate-msg.sh` は、次の値を使って初期残高と minter を含む JSON を作成する。
`CREATOR_ADDR` が未設定の場合は、鍵からアドレスを取得する。

```bash
OUTPUT_FILE="${OUTPUT_FILE:-instantiate_msg.json}"
TOKEN_NAME="${TOKEN_NAME:-My Token}"
TOKEN_SYMBOL="${TOKEN_SYMBOL:-MTK}"
TOKEN_DECIMALS="${TOKEN_DECIMALS:-6}"
INITIAL_BALANCE="${INITIAL_BALANCE:-1000000}"
if ! echo "$TOKEN_SYMBOL" | grep -Eq '^[A-Za-z-]{3,12}$'; then
  echo "symbol は英字またはハイフンの3〜12文字で指定してください" >&2
  exit 1
fi
if [ -z "${CREATOR_ADDR:-}" ]; then
  CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
fi

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
