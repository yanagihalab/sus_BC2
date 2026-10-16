# injectived の設定・操作手順

本書は、利用可能な CLI `injectived` がある環境を前提として、Injective Testnet への接続設定、鍵・ウォレットの管理、トランザクションの送信・確認を説明する。
共通の環境構築は、[メイン README](../README.md) を参照する。

本書のコマンドは、特に指定がない限り、Kali Linux のターミナルでリポジトリルートから実行する。パスは標準配置の例であり、作業先を変更した場合は読み替える。

以下は同じ Bash セッションで、番号順に実行する。初期設定では、送信元・受取先の両方に自分の `testwallet` を使用する。作成済みのウォレットを使う場合は、その鍵名を指定する。新しいウォレットを作る場合は、未使用の鍵名を指定する。
書き込み操作ごとに返された TxHash を照会し、ブロックへの取り込みと `code: 0` を確認してから次へ進む。Faucet での入金はブラウザで行い、コード中の TxHash・code ID・コントラクトアドレスは、その操作の実際の結果に置き換える。

## 1. 接続設定を読み込む

リポジトリへ移動して接続先と鍵名を設定し、`load-env.sh` で共通設定を読み込む。前回のアドレス・識別子は `unset` で解除する。

```bash
cd ~/temp/sus_BC2
# 使用する鍵名を指定する。新しいウォレットを作る場合は未使用の名前に変更する。
export KEY_NAME="testwallet"
export KEYRING_BACKEND="test"
# 接続するチェーンの ID と RPC URL を指定する。
export CHAIN_ID="injective-888"
export NODE="https://injective-testnet-rpc.publicnode.com:443"
export GAS_PRICES="500000000inj"
export GAS=1000000
export BANK_SEND_GAS=200000
unset MY_ADDR ADDR RECIPIENT_ADDR CREATOR_ADDR SENDER_ADDR DENOM CODE_ID CONTRACT_ADDR
source scripts/injectived/load-env.sh
```

`load-env.sh` は既存の設定値を保持する。接続先や鍵を変更するときは、上の値を変更して読み込み直す。

## 2. ウォレットを作成し、アドレスを取得する

手順 1 で設定した鍵名と keyring backend を使い、自分のウォレットを作成する。そのアドレスを送信元と受取先に設定する。作成済みのウォレットを使う場合は、最初の `injectived keys add` の行を省略する。

```bash
# 作成済みのウォレットを使う場合は、次の keys add の行を省略する。
injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
export MY_ADDR
export ADDR="$MY_ADDR"
export RECIPIENT_ADDR="$MY_ADDR"
injectived keys list --keyring-backend "$KEYRING_BACKEND"
printf 'Sender: %s\nRecipient: %s\n' "$MY_ADDR" "$RECIPIENT_ADDR"
```

`MY_ADDR` と `ADDR` は自分のアドレス、`RECIPIENT_ADDR` は送金先である。初期設定では同じアドレスを使う。表示の `Sender` は送信元、`Recipient` は受取先を表す。
作成された鍵を使って、後続の送金・トークン作成・コントラクト操作を行う。新しいターミナルを開いた場合は、手順 1・2 を実行し直す。

<details>
<summary>補足：環境変数の読み込みとウォレット作成のコマンド</summary>

#### 環境変数の設定

`load-env.sh` は `source` で読み込み、現在のシェルに `export` で値を設定する。すでに設定した値は保持される。
ウォレット作成後に、接続設定とアドレスを手動で設定する場合は次のように実行する。

```bash
# 使用する鍵名を指定する。新しいウォレットを作る場合は未使用の名前に変更する。
export KEY_NAME="testwallet"
export KEYRING_BACKEND="test"
# 接続するチェーンの ID と RPC URL を指定する。
export CHAIN_ID="injective-888"
export NODE="https://injective-testnet-rpc.publicnode.com:443"
export GAS_PRICES="500000000inj"
export GAS=1000000
export BANK_SEND_GAS=200000
export AMOUNT="100000000inj"
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
export MY_ADDR
export ADDR="$MY_ADDR"
export RECIPIENT_ADDR="$MY_ADDR"
```

`KEY_NAME` は使用する鍵の名前、`CHAIN_ID` と `NODE` は接続先、`GAS_PRICES` はガス単価である。
`GAS` はガス上限、`BANK_SEND_GAS` は INJ 送金用のガス上限、`AMOUNT` は送金量、`RECIPIENT_ADDR` は送金先を表す。上の例では、自分の `MY_ADDR` を送金先に設定する。
`KEYRING_BACKEND` は鍵の保存方式を指定する。`keys show -a` は、鍵に対応するアドレスを取得する。
アドレスはウォレットを作成してから取得する。

#### ウォレットの作成とアドレス取得

ウォレットの作成には `keys add`、アドレスの取得には `keys show -a` を使う。

```bash
# 作成済みのウォレットを使う場合は、次の keys add の行を省略する。
injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
export MY_ADDR
```

作成済みの鍵を一覧で確認し、使用する鍵のアドレスを取得する場合は、次を実行する。

```bash
injectived keys list --keyring-backend "$KEYRING_BACKEND"
injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND"
```

`keys add` は鍵とウォレットを作成する。作成後の `MY_ADDR` を Faucet や残高照会に使用する。

</details>

## 3. Faucet で INJ を取得し、残高を確認する

`MY_ADDR` を表示し、[Injective testnet の Faucet](https://cloud.google.com/application/web3/faucet/injective/testnet) に入力して INJ を取得する。この入金操作はブラウザで行う。
送金量に加え、後続のトークン作成・コード登録に必要な手数料を支払える残高を確認する。

```bash
echo "$MY_ADDR"
injectived query bank balances "$MY_ADDR" \
  --node="$NODE" --chain-id="$CHAIN_ID" --output json | jq
```

## 4. INJを送金する

初期設定の宛先は自分の `MY_ADDR` である。この手順では別の宛先へ `0.001 INJ` を送金するため、実際の受取アドレスを `RECIPIENT_ADDR` に設定する。

```bash
# 二重引用符の間に実際の受取アドレスを入力してから実行する。
export RECIPIENT_ADDR=""
```

設定した受取アドレスを確認する。

```bash
echo "RECIPIENT_ADDR=$RECIPIENT_ADDR"
```

後続の INJ・TokenFactory・CW20 の送金では、この `RECIPIENT_ADDR` を使う。

設定した宛先へ送金する。

```bash
# 送金量を inj 単位で指定する。この例は 0.001 INJ。
export AMOUNT="1000000000000000inj"
export BANK_SEND_GAS=200000
CONFIRM_SEND=yes bash ./scripts/injectived/bank-send.sh
```

返された TxHash を控え、次の手順で送金結果を確認する。

<details>
<summary>補足：bank-send.sh が実行する送金コマンド</summary>

以下は、`bank-send.sh` の送金処理を CLI で直接実行する場合の例である。送信元の鍵、送金先、送金量を指定して INJ を送金する。受取先が未設定または空の場合は、自分のアドレスを使う。

```bash
RECIPIENT_ADDR="${RECIPIENT_ADDR:-$MY_ADDR}"
AMOUNT="100000000inj"
BANK_SEND_GAS="${BANK_SEND_GAS:-${GAS:-200000}}"
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$BANK_SEND_GAS" \
  --broadcast-mode sync \
  -y
```

`--from` は署名に使う鍵、`--chain-id` と `--node` は接続先を指定する。
`--gas-prices` と `--gas` は手数料計算に使う設定である。送金には `BANK_SEND_GAS` を使う。
`--broadcast-mode sync` はトランザクションを送信して応答を受け取る方式で、ブロックへの取り込み結果は TxHash で別途確認する。
`-y` は CLI の確認を自動承認する指定である。
`CONFIRM_SEND=yes` は補助スクリプト内の実行条件であり、直接 `injectived` を実行する場合のオプションではない。
`inj` は INJ の最小単位で、`1000000000000000000inj` が `1 INJ` に相当する。過去の送金例で使った `1000000000000000inj` は `0.001 INJ` である。送金量は使用する `AMOUNT` の値で指定する。

</details>

<details>
<summary>補足：test keyring を指定した過去の送金記録</summary>

過去の手順では、鍵名と keyring backend の指定に不一致があった。現行の手順は既定の鍵名を `testwallet`、`KEYRING_BACKEND` を `test` に統一し、鍵の取得と送金の両方で同じ保存方式を指定する。
設定は `source scripts/injectived/load-env.sh` で読み込み、次のコマンドで鍵情報と残高を確認できる。

```bash
echo "KEY_NAME=$KEY_NAME"
injectived keys show "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
injectived query bank balances "$MY_ADDR" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE"
```

以下は、過去の記録の出力構造を示したものである。アドレス、公開鍵、TxHash は例示用の表記に置き換えている。

```text
KEY_NAME=testwallet
- address: inj...
  name: testwallet
  pubkey: '{"@type":"/injective.crypto.v1beta1.ethsecp256k1.PubKey","key":"公開鍵"}'
  type: local
```

次は、銀行残高を照会した応答例である。`denom` が通貨の識別子、`amount` がその通貨の最小単位での残高を表す。

```yaml
balances:
- amount: "10000000000000000000"
  denom: inj
pagination:
  total: "1"
```

`100000000inj`、ガス上限 `200000`、`--keyring-backend test`、`--broadcast-mode sync` を指定した送金時の応答例は次のとおりである。

```yaml
code: 0
codespace: ""
data: ""
events: []
gas_used: "0"
gas_wanted: "0"
height: "0"
info: ""
logs: []
raw_log: ""
timestamp: ""
tx: null
txhash: 記録のTxHash
```

この応答はブロードキャスト時の記録であり、ブロックへの取り込み後の確定結果ではない。送金結果は、手順 5 のトランザクション確認に従って別途確認する。

</details>

### 4.1. INJ 送金の TxHash 応答時間を計測する

必須課題 1-6 の計測には、[1-6_inj-transfer-time.py](../Day1/1-6_inj-transfer-time.py) を使う。1回の実行で1回送金し、コマンドの起動直前から、TxHash を含む応答を受信してコマンドが終了するまでの秒数を表示する。
計測値には CLI の起動・署名・RPC 通信・受付応答の待ち時間を含む。`sync` はトランザクションの受付結果を返す方式であり、ブロックへの取り込みは手順 5 または Explorer で確認する。[Cosmos SDK の同期送信処理](https://github.com/cosmos/cosmos-sdk/blob/v0.50.13/client/broadcast.go#L79-L93)

送信元には、手順 1・2 で作成したウォレットをそのまま使う。計測コードは、現在の Bash セッションの `KEY_NAME`（鍵名）と `KEYRING_BACKEND`（鍵の保存方式）を引き継ぐ。標準設定では `testwallet` と `test` を使う。
ウォレットを作成した Kali Linux の同じユーザーで実行する。新しいターミナルを開いた場合は、手順 1・2 を実行し直し、作成済みのため `injectived keys add` の行は省略する。

手順 1〜3 の準備を済ませ、手順 4 の受取アドレス設定まで実行する。送金は、この節の計測コマンドで行う。計測前に、送信元の鍵名・保存方式・アドレスと、共同実験者の受取アドレスを確認する。

```bash
echo "KEY_NAME=$KEY_NAME"
echo "KEYRING_BACKEND=$KEYRING_BACKEND"
injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND"
echo "RECIPIENT_ADDR=$RECIPIENT_ADDR"
```

送金量とガス上限を設定し、計測付きで1回送金する。

```bash
# 送金量を inj 単位で指定する。この例は 0.001 INJ。
export AMOUNT="1000000000000000inj"
export BANK_SEND_GAS=200000
CONFIRM_SEND=yes python3 Day1/1-6_inj-transfer-time.py
```

CLI の JSON 応答にある `txhash` がその回の TxHash、末尾の `Response time` がコマンドの応答時間（秒）を表す。結果は端末に表示する。
各回の TxHash で送金結果を確認してから、同じ計測コマンドを10回以上実行する。表示された TxHash と時間を報告書に記録し、CLI が正常に終了して応答の `code` が `0` で、TxHash を確認できた回の時間から平均を求める。

<details>
<summary>補足：計測コードの設定と処理順序</summary>

計測コードは Python の標準ライブラリを使い、次の環境変数を送金コマンドに渡す。

| 環境変数 | 対応する設定値 | 未設定または空欄の場合の値 |
| --- | --- | --- |
| `KEY_NAME` | 送信元の鍵名 | `testwallet` |
| `KEYRING_BACKEND` | 鍵の保存方式。対話入力のない `test` を使う | `test` |
| `CHAIN_ID` | 接続するチェーンの ID | `injective-888` |
| `NODE` | 接続先の RPC URL | `https://injective-testnet-rpc.publicnode.com:443` |
| `GAS_PRICES` | ガス単価 | `500000000inj` |
| `BANK_SEND_GAS` | 送金のガス上限 | `200000` |
| `AMOUNT` | 最小単位で指定する INJ の送金量 | `1000000000000000inj`（`0.001 INJ`） |
| `RECIPIENT_ADDR` | 共同実験者の受取アドレス | 必ず設定する |
| `CONFIRM_SEND` | 送金を実行する指定 | 実行時に `yes` を渡す |

処理は次の順に実行する。

1. 環境変数と CLI の制限時間を確認する。
2. `time.perf_counter()` で計測を始め、`injectived tx bank send` を `--broadcast-mode sync --output json -y` 付きで1回実行する。CLI の標準出力・標準エラーはそのまま端末に表示する。
3. コマンドが終了した直後に計測を終え、経過秒数を `Response time` として表示する。

送金の受付結果は CLI 応答の `code` で確認し、ブロックへの取り込み結果は TxHash で確認する。タイムアウト・中断の場合も、表示された応答を確認してから次の送金を行う。コードは送信を自動で再試行しない。

CLI の制限時間を変更する場合は、次のように指定する。

```bash
# --timeout に制限時間を秒数で指定する。
CONFIRM_SEND=yes python3 Day1/1-6_inj-transfer-time.py --timeout 60
```

</details>

## 5. トランザクションの成功を確認する

送金、TokenFactory、CW20 などの書き込み操作の結果を照会するため、`check_tx` 関数を定義する。このブロックでは関数を定義するだけで、照会は実行しない。
照会結果では、ブロックに取り込まれ、`code` が `0` であることを確認する。
`--broadcast-mode sync` の応答で `code: 0` と TxHash が返っても、`height: "0"` であれば確定成功を示すものではない。ブロックへの取り込み後、TxHash で結果を確認する。

```bash
check_tx() {
  local tx_result
  tx_result="$(injectived q tx "$1" \
    --chain-id="$CHAIN_ID" \
    --node="$NODE" \
    --output json)" || return
  printf '%s\n' "$tx_result" | jq
}
```

手順 4 の INJ 送金で返された TxHash を使い、送金結果を照会する。

```bash
# INJ 送金で返された TxHash を、次の空の二重引用符の間に入力してから実行する。
check_tx ""
```

以降の `check_tx` も、空の二重引用符の間に、その操作で返された実際の TxHash を手入力してから実行する。まだ見つからない場合は、数秒待って同じ照会コマンドを再実行する。

トランザクションは、次の Explorer でも確認できる。

- [Mintscan（Injective Testnet）](https://www.mintscan.io/injective-testnet)
- [Injective Testnet Explorer](https://testnet.explorer.injective.network/)

## 6. TokenFactory で MTK を作成・送金する

### 6.1. 設定を読み込み、denom を作成する

同じ鍵・subdenom の組み合わせでの作成は一度だけ行う。作成済みなら作成コマンドを省略するか、`SUBDENOM` を未使用の名前に変更する。
名称・シンボル・小数桁数を変更する場合は、次の設定値を編集する。新規作成時の小数桁数は [0〜24 の範囲](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/types/denoms.go)で指定する。本書の数量例は `6` 桁を前提としている。

トークンの設定を読み込み、自分のアドレスを作成者として denom の作成トランザクションを送信する。

```bash
# 必要に応じて、二重引用符の間の値をトークンの名称に変更する。
export TOKEN_NAME="My Token"
# 必要に応じて、二重引用符の間の値をトークンのシンボルに変更する。
export TOKEN_SYMBOL="MTK"
# 小数桁数を指定する。メタデータ編集時は作成時と同じ値を使う。
export TOKEN_DECIMALS=6
export GAS=300000
# 新規作成時は未使用の名前を指定する。既存トークンの編集では作成時の値を使う。
export SUBDENOM="mtk"
export CREATOR_ADDR="$MY_ADDR"
export DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
source scripts/tokenfactory/load-env.sh
CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh create-denom
```

denom の作成結果を照会し、作成が成功したことを確認する。

```bash
# denom 作成で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

### 6.2. メタデータを設定する

変更したい値を編集し、同じ Bash で設定する。作成済みトークンのメタデータを編集する場合も、この設定と次の `set-metadata` を実行する。denom の作成コマンドを再実行する必要はない。

```bash
# 必要に応じて、二重引用符の間の値をトークンの名称に変更する。
export TOKEN_NAME="My Token"
# 必要に応じて、二重引用符の間の値をトークンのシンボルに変更する。
export TOKEN_SYMBOL="MTK"
# 説明文を入力する。説明を削除する場合は二重引用符の間を空にする。
export TOKEN_DESCRIPTION="My Token Description"
# 表示単位を入力する。0 桁の場合は二重引用符の間を $DENOM に変更する。
export TOKEN_DISPLAY="MTK"
# 小数桁数を指定する。メタデータ編集時は作成時と同じ値を使う。
export TOKEN_DECIMALS=6
# 参照先 URI を指定する場合は二重引用符の間に入力する。使用しない場合は空のままにする。
export TOKEN_URI=""
# URI のハッシュを指定する場合は二重引用符の間に入力する。使用しない場合は空のままにする。
export TOKEN_URI_HASH=""
```

| 変数 | 編集する内容 |
| --- | --- |
| `TOKEN_NAME` | トークンの名称 |
| `TOKEN_SYMBOL` | シンボル |
| `TOKEN_DESCRIPTION` | 説明文。空文字で削除できる |
| `TOKEN_DISPLAY` | 表示単位の denom。未指定の場合はシンボルを使う |
| `TOKEN_DECIMALS` | 表示単位の小数桁数。作成時と同じ値を使う |
| `TOKEN_URI`・`TOKEN_URI_HASH` | メタデータの参照先とハッシュ。使用しない場合は空文字にする |

編集対象の `KEY_NAME`・`SUBDENOM` を引き継ぎ、管理者の鍵で実行する。表示名やシンボルを編集しても、対象の `factory/作成者アドレス/subdenom` は変更しない。
`TOKEN_DECIMALS=0` の場合は `TOKEN_DISPLAY="$DENOM"` とする。表示単位を省略した場合も、0桁では最小単位の denom を使う。小数桁数を変更して新規作成する場合は、以降のミント・送金量もその桁数に合わせる。

`set-metadata` は、使用中の CLI の Usage を確認して末尾引数を選ぶ。
[公式 v1.18.0 の CLI](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) は末尾に `[decimals] [shouldDisableAdminBurn]` を取り、[公式ガイド](https://docs.injective.network/developers-defi/token-launch) は `[decimals]` のみの例を掲載している。補助スクリプトは `TOKEN_DECIMALS` と `false`、または `TOKEN_DECIMALS` のみを渡し、どちらにも一致しない場合やヘルプ取得に失敗した場合は送信せず停止する。

設定した名称・説明・表示単位などを、対象の `DENOM` のメタデータとして登録・更新する。

```bash
CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh set-metadata
```

<details>
<summary>補足：メタデータ設定を CLI で直接実行する場合</summary>

補助スクリプトの代わりに次の関数を実行できる。手順 6.2 で設定した値を使い、補助スクリプトと同じ Usage の判定で末尾引数を選ぶ。上の `set-metadata` とこの代替コマンドの両方を実行する必要はない。

```bash
set_token_metadata() {
  local metadata_help
  local metadata_args
  local metadata_units
  metadata_units="$(jq -cn \
    --arg base "$DENOM" --arg display "$TOKEN_DISPLAY" \
    --argjson decimals "$TOKEN_DECIMALS" \
    '[{denom:$base,exponent:0,aliases:[]}] +
     (if $display == $base then []
      else [{denom:$display,exponent:$decimals,aliases:[]}] end)')" || return
  metadata_help="$(injectived tx tokenfactory set-denom-metadata --help)" || return
  printf '%s\n' "$metadata_help"
  if grep -Fq '[shouldDisableAdminBurn]' <<< "$metadata_help"; then
    metadata_args=("$TOKEN_DECIMALS" false)
  elif grep -Eq 'set-denom-metadata .*\[decimals\]([[:space:]]+\[flags\])?[[:space:]]*$' <<< "$metadata_help"; then
    metadata_args=("$TOKEN_DECIMALS")
  else
    echo "Unsupported metadata arguments. Check the CLI Usage." >&2
    return 1
  fi
  injectived tx tokenfactory set-denom-metadata \
    "$TOKEN_DESCRIPTION" "$DENOM" "$TOKEN_DISPLAY" "$TOKEN_NAME" "$TOKEN_SYMBOL" \
    "$TOKEN_URI" "$TOKEN_URI_HASH" "$metadata_units" \
    "${metadata_args[@]}" \
    --from="$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
    --chain-id="$CHAIN_ID" --node="$NODE" \
    --gas-prices="$GAS_PRICES" --gas="$GAS" -y
}
set_token_metadata
```

</details>

メタデータの登録・更新結果を照会し、トランザクションが成功したことを確認する。

```bash
# メタデータ設定で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

確定成功を確認したら、対象の `DENOM` に登録されたメタデータを照会する。

```bash
injectived query bank denom-metadata "$DENOM" \
  --chain-id="$CHAIN_ID" --node="$NODE" --output json | jq
```

出力の `metadata` にある `name`・`symbol`・`description`・`display`・`denom_units`・`decimals`・`uri`・`uri_hash` が、設定した内容と一致することを確認する。

### 6.3. MTK をミントする

指定した数量の MTK を発行し、作成者のアドレスに付与する。小数桁数 `6` の場合、`1000000000` は `1000 MTK` に相当する。

```bash
# ミント量を最小単位で指定する。必要に応じて MINT_AMOUNT の値を変更する。
MINT_AMOUNT=1000000000 CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh mint
```

ミントの結果を照会し、トランザクションが成功したことを確認する。

```bash
# MTK のミントで返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

### 6.4. 残高を確認する

作成者のアドレスの銀行残高を照会し、作成した MTK の denom と数量を確認する。

```bash
bash ./setup/normal/07-tokenfactory-mtk.sh balance
```

### 6.5. MTK を送金し、受取先の残高を確認する

手順 4 で設定した受取アドレス（`RECIPIENT_ADDR`）へ、`SEND_AMOUNT` で指定した数量の MTK を送金する。

```bash
# 送金量を最小単位で指定する。必要に応じて値を変更する。
export SEND_AMOUNT=1000000
CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh send
```

MTK の送金結果を照会し、トランザクションが成功したことを確認する。

```bash
# MTK の送金で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

送金の成功を確認したら、受取アドレス（`RECIPIENT_ADDR`）の銀行残高を照会し、MTK の残高を確認する。

```bash
injectived query bank balances "$RECIPIENT_ADDR" \
  --node="$NODE" --chain-id="$CHAIN_ID" --output json | jq
```

各補助スクリプトの内部コマンドと設定値は、次の補足で確認できる。

<details>
<summary>補足：TokenFactory の環境設定と各操作のコマンド</summary>

#### 環境変数と denom の組み立て

鍵名、チェーン、RPC、ガス単価、鍵の保存方式は Injective の共通設定と同じである。
TokenFactory 用の `load-env.sh` は、次の固有設定を読み込む。

```bash
export GAS="${GAS:-300000}"
export SUBDENOM="${SUBDENOM:-mtk}"
export SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
if command -v injectived >/dev/null 2>&1; then
  export CREATOR_ADDR="${CREATOR_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export CREATOR_ADDR="${CREATOR_ADDR:-}"
fi
if [ -n "$CREATOR_ADDR" ]; then
  export DENOM="${DENOM:-factory/${CREATOR_ADDR}/${SUBDENOM}}"
else
  export DENOM="${DENOM:-}"
fi
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-$CREATOR_ADDR}"
```

`CREATOR_ADDR` は作成者のアドレス、`SUBDENOM` はトークン名の末尾部分である。
完全な denom は `factory/作成者アドレス/subdenom` の形式になる。
`RECIPIENT_ADDR` が未設定または空の場合は、自分の `CREATOR_ADDR` を送金先とする。明示した送金先は保持される。
補助スクリプトの各操作では、鍵からアドレスを取得し、denom を組み立て直す。
以下の手動例も、使用する鍵から値を取得する。ガス上限の例は `300000` とする。

```bash
GAS=300000
CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
```

`load-env.sh` は既存の `GAS` を保持するため、操作に合わせてガス値を指定する。
`CREATOR_ADDR` や `DENOM` も既存の値を保持する。使用する鍵や subdenom を変更した場合は、上記の手動例でアドレスと denom を取得し直す。

`set-denom-metadata` が `invalid metadata base denom: invalid denom:` で失敗する場合は、まず `DENOM` が空になっていないか確認する。

```bash
echo "DENOM=[$DENOM]"
```

正しい表示形式は次のとおりである。

```text
DENOM=[factory/inj.../mtk]
```

`bash ./setup/normal/07-tokenfactory-mtk.sh env` は設定を画面に表示する操作であり、現在のシェルへの読み込みは `source` で行う。

#### denom の作成

`create-denom` では、subdenom、名称、記号、小数桁数を指定する。

```bash
injectived tx tokenfactory create-denom \
  "$SUBDENOM" "$TOKEN_NAME" "$TOKEN_SYMBOL" "$TOKEN_DECIMALS" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

作成トランザクションの成功を確認してから、以降の操作へ進む。

#### メタデータの設定

名称、説明、表示単位などを登録する。実行には手順 6.2 の設定値を編集し、`set-metadata` または CLI の直接実行例を使用する。

単位の JSON は設定値から組み立てる。最小単位の exponent は `0`、別の表示単位の exponent は `TOKEN_DECIMALS` とする。表示単位が最小単位と同じ場合は1件にまとめる。
[公式の公開ソース v1.18.0](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) では、末尾2引数は `decimals` と `shouldDisableAdminBurn` である。
この仕様では末尾に `TOKEN_DECIMALS` と `false` を渡す。
[公式のトークン作成ガイド](https://docs.injective.network/developers-defi/token-launch) の9引数の例では、末尾に小数桁数のみを渡す。補助スクリプトは、次のコマンドの Usage を確認して引数を切り替える。

```bash
injectived tx tokenfactory set-denom-metadata --help
```

Usage に想定した末尾引数が見つからない場合は送信せず停止する。小数桁数には作成時と同じ値を使う。

#### ミント・残高確認・送金

数量と denom を連結して MTK を発行し、作成者アドレス（`CREATOR_ADDR`）に付与する。

```bash
MINT_AMOUNT="${MINT_AMOUNT:-1000000000}"
injectived tx tokenfactory mint "${MINT_AMOUNT}${DENOM}" "$CREATOR_ADDR" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

`MINT_AMOUNT` は最小単位の数量で、変数自体には denom を含めない。
小数桁数が `6` の場合、既定の `1000000000` は `1000 MTK` に相当する。
次のコマンドは、作成者の銀行残高を JSON で取得する。

```bash
injectived query bank balances "$CREATOR_ADDR" \
  --node="$NODE" --chain-id="$CHAIN_ID" -o json | jq
```

送金は、宛先と最小単位の数量を設定してから実行する。初期設定の宛先は自分のアドレスである。小数桁数が `6` の場合、既定の `SEND_AMOUNT=1000000` は `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="${RECIPIENT_ADDR:-$CREATOR_ADDR}"
SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "${SEND_AMOUNT}${DENOM}" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

`CONFIRM_TX=yes` は補助スクリプト側の実行条件である。直接 CLI を使う場合は、上記のコマンドで処理を実行する。
各書き込み操作の結果は、返された TxHash で確認する。

</details>

## 7. CW20 のコード登録・初期化・送金・ミントを行う

登録する WASM ファイルは、[メイン README の CW20 ビルドの補足](../README.md#cw20-サンプルの取得と-wasm-のビルド) に従って準備しておく。

### 7.1. 設定を読み込み、WASM を登録する

署名者とガス上限を設定して CW20 用の環境変数を読み込み、署名者のアドレスと WASM ファイルのパスを表示する。その後、WASM をチェーンへ登録する。

この手順以降で共通して使う環境変数は、次の設定に対応する。接続先と鍵の設定は、手順 1 の値を引き継ぐ。

| 環境変数 | 対応する設定値・用途 |
| --- | --- |
| `KEY_NAME` | 操作に署名するウォレットの鍵名。`--from` に渡す |
| `KEYRING_BACKEND` | 鍵の保存方式。`--keyring-backend` に渡す |
| `CHAIN_ID` | 接続するチェーンの ID。`--chain-id` に渡す |
| `NODE` | 接続先の RPC URL。`--node` に渡す |
| `GAS_PRICES` | ガス単価。`--gas-prices` に渡す |
| `GAS` | ガス上限。`--gas` に渡す。コード登録では `3000000`、手順 7.4 以降では `300000` を指定する |
| `MY_ADDR` | 手順 2 で取得した自分のウォレットアドレス。下の例で `SENDER_ADDR` と `CREATOR_ADDR` に設定する |
| `SENDER_ADDR` | 自分のアドレス。署名者の表示、残高照会、ミントの受取先に使う。署名に使う鍵は `KEY_NAME` で指定する |
| `CREATOR_ADDR` | 初期残高の受取先と追加発行者（minter）に設定するアドレス |
| `WASM_PATH` | チェーンに登録する WASM ファイルのパス。`wasm store` に渡す |
| `CONFIRM_TX` | 補助スクリプトで書き込み処理を実行するための指定。実行時に `yes` を渡す |

```bash
export GAS=3000000
export SENDER_ADDR="$MY_ADDR"
export CREATOR_ADDR="$MY_ADDR"
source scripts/CW20/load-env.sh
printf 'Signer: %s\nWASM: %s\n' "$SENDER_ADDR" "$WASM_PATH"
CONFIRM_TX=yes bash ./setup/normal/11-store-cw20-code.sh
```

CLI の実行確認が表示されたら、内容を確認して `y` を入力し、`Enter` を押す。
表示の `Signer` は署名者のアドレス、`WASM` は登録するファイルのパスを表す。

### 7.2. 登録結果を確認し、code ID を設定する

WASM 登録で返された TxHash を使い、登録が成功したことを確認する。

```bash
# WASM 登録で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

成功した登録結果の `events` から `code_id` を読み取り、初期化に使う `CODE_ID` に設定する。`CODE_ID` は登録済みの WASM コードを識別する番号で、手順 7.4 の `wasm instantiate` に渡す。

```bash
# 成功したトランザクションの events にある code_id を読み取り、二重引用符の間に入力してから実行する。
export CODE_ID=""
```

### 7.3. 初期化メッセージを作成する

トークンの名称・シンボル・小数桁数・初期残高を指定して `instantiate_msg.json` を生成し、`jq` で内容を表示する。

各変数と、生成する JSON の設定値の対応は次のとおりである。

| 環境変数 | 対応する JSON 項目・用途 | この例の値 |
| --- | --- | --- |
| `TOKEN_NAME` | `name`：トークンの名称 | `My Token` |
| `TOKEN_SYMBOL` | `symbol`：トークンのシンボル | `MTK` |
| `TOKEN_DECIMALS` | `decimals`：表示時の小数桁数 | `6` |
| `INITIAL_BALANCE` | `initial_balances[].amount`：最小単位での初期残高 | `1000000`（小数桁数 `6` では `1 MTK`） |
| `CREATOR_ADDR` | `initial_balances[].address`：初期残高の受取先、`mint.minter`：追加発行者のアドレス | 手順 7.1 で設定した自分の `MY_ADDR` |
| `OUTPUT_FILE` | 生成した JSON の保存先ファイル名 | `instantiate_msg.json` |

```bash
# 必要に応じて、名称・シンボル・小数桁数・初期残高を変更する。
TOKEN_NAME="My Token" TOKEN_SYMBOL="MTK" TOKEN_DECIMALS=6 INITIAL_BALANCE=1000000 OUTPUT_FILE=instantiate_msg.json \
  bash ./scripts/CW20/create-instantiate-msg.sh
jq . instantiate_msg.json
```

JSON の初期残高と minter のアドレスが `CREATOR_ADDR` と一致することを確認する。生成処理の詳細は、[CW20 初期化メッセージの作成](cw20-instantiate-message.md) を参照する。

### 7.4. コントラクトを初期化する

コード登録用のガス値から、以降の操作の値へ切り替える。`CODE_ID` のコードと `instantiate_msg.json` を使い、CW20 コントラクトを作成する。

```bash
export GAS=300000
injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" --node="$NODE" \
  --label "cw20-mtk-sample" --no-admin \
  --gas-prices="$GAS_PRICES" --gas="$GAS" --output json -y
```

初期化の結果を照会し、コントラクトの作成が成功したことを確認する。

```bash
# 初期化で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

### 7.5. コントラクトアドレスを設定する

手順 7.4 の成功した初期化結果からコントラクトアドレスを読み取り、以降の照会・送金・ミントに使う `CONTRACT_ADDR` に設定する。`CONTRACT_ADDR` は、`wasm contract-state smart` と `wasm execute` の操作対象を指定する。

```bash
# 成功したトランザクションの events にある _contract_address または contract_address を読み取り、二重引用符の間に入力してから実行する。
export CONTRACT_ADDR=""
```

### 7.6. トークン情報と残高を確認する

`CONTRACT_ADDR` のコントラクトに対し、1つ目のコマンドで CW20 トークンの情報を、2つ目で自分のアドレス（`SENDER_ADDR`）の CW20 トークン残高を照会する。

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' --node "$NODE" --output json | jq
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' --node "$NODE" --output json | jq
```

### 7.7. CW20 トークンを送金する

CW20 トークンの受取アドレスを `RECIPIENT_ADDR` に設定する。

```bash
# 二重引用符の間に実際の受取アドレスを入力してから実行する。
export RECIPIENT_ADDR=""
```

設定した宛先へ送金する。

| 環境変数 | 対応する送金の設定値 |
| --- | --- |
| `CONTRACT_ADDR` | 操作対象の CW20 コントラクトのアドレス |
| `RECIPIENT_ADDR` | `transfer.recipient`：トークンの受取アドレス |
| `CW20_SEND_AMOUNT` | `transfer.amount`：最小単位での送金量。この例は `1000000`（小数桁数 `6` では `1 MTK`） |

```bash
# CW20 の送金量を最小単位で指定する。必要に応じて値を変更する。
export CW20_SEND_AMOUNT=1000000
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" --node "$NODE" \
  --gas-prices "$GAS_PRICES" --gas "$GAS" --output json -y
```

CW20 の送金結果を照会し、トランザクションが成功したことを確認する。

```bash
# CW20 の送金で返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

送金の成功を確認したら、受取アドレス（`RECIPIENT_ADDR`）の CW20 トークン残高を確認する。

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$RECIPIENT_ADDR"'"}}' --node "$NODE" --output json | jq
```

### 7.8. CW20 トークンをミントする

初期化メッセージで minter に設定した `KEY_NAME` の鍵で実行する。`CW20_MINT_AMOUNT` で指定した数量を発行し、`SENDER_ADDR` に付与する。

| 環境変数 | 対応するミントの設定値 |
| --- | --- |
| `CONTRACT_ADDR` | 操作対象の CW20 コントラクトのアドレス |
| `SENDER_ADDR` | `mint.recipient`：発行したトークンの受取アドレス |
| `CW20_MINT_AMOUNT` | `mint.amount`：最小単位での発行量。この例は `1000000`（小数桁数 `6` では `1 MTK`） |

```bash
# CW20 のミント量を最小単位で指定する。必要に応じて値を変更する。
export CW20_MINT_AMOUNT=1000000
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$SENDER_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" --node "$NODE" \
  --gas-prices "$GAS_PRICES" --gas "$GAS" --output json -y
```

CW20 のミント結果を照会し、トランザクションが成功したことを確認する。

```bash
# CW20 のミントで返された TxHash を、二重引用符の間に入力してから実行する。
check_tx ""
```

ミントの成功を確認したら、発行先アドレス（`SENDER_ADDR`）の CW20 トークン残高を確認する。

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' --node "$NODE" --output json | jq
```

<details>
<summary>補足：CW20 の環境設定・コード登録・初期化・照会・送金・ミント</summary>

#### 環境変数とコード登録

CW20 用の `load-env.sh` は共通の鍵・接続設定に加え、次の保存先と操作用の変数を設定する。
`GAS` と同様に、`SENDER_ADDR`、`CODE_ID`、`CONTRACT_ADDR` などの既存値は保持される。鍵や対象コントラクトを変えた場合は、対応する値を設定し直してから読み込む。

WASM ファイルのパスを組み立てる変数は、次の設定に対応する。

| 環境変数 | 対応する設定値 | 未設定または空欄の場合の値 |
| --- | --- | --- |
| `WORKDIR` | CW20 サンプルを配置する作業ディレクトリ | `$HOME/temp` |
| `CW_PLUS_DIR` | `cw-plus` ソースのディレクトリ | `$WORKDIR/cw-plus` |
| `WASM_PATH` | 登録する WASM ファイルのパス | `$CW_PLUS_DIR/artifacts/cw20_base.wasm` |

`HOME` は、現在のユーザーのホームディレクトリを表す。

```bash
export GAS="${GAS:-300000}"
export WORKDIR="${WORKDIR:-$HOME/temp}"
export CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"
export WASM_PATH="${WASM_PATH:-$CW_PLUS_DIR/artifacts/cw20_base.wasm}"
export CODE_ID="${CODE_ID:-}"
export CONTRACT_ADDR="${CONTRACT_ADDR:-}"
export CW20_SEND_AMOUNT="${CW20_SEND_AMOUNT:-1000000}"
export CW20_MINT_AMOUNT="${CW20_MINT_AMOUNT:-1000000}"
if command -v injectived >/dev/null 2>&1; then
  export SENDER_ADDR="${SENDER_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export SENDER_ADDR="${SENDER_ADDR:-}"
fi
export MY_ADDR="${MY_ADDR:-$SENDER_ADDR}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-$SENDER_ADDR}"
```

`WASM_PATH` はビルド済みコードの保存先である。
`RECIPIENT_ADDR` が未設定または空の場合は、自分の `SENDER_ADDR` を送金先とする。明示した送金先は保持される。
`11-store-cw20-code.sh` は、このファイルの存在と `CONFIRM_TX=yes` を確認した後、次の登録コマンドを実行する。
以下の手動例では、コード登録用のガス上限を明示している。

```bash
GAS=3000000
injectived tx wasm store "$WASM_PATH" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS"
```

`store` は WASM コードをチェーンへ登録する操作で、成功後に code ID を取得できる。
このコマンドには `-y` がないため、CLI の確認に応答して実行する。
`CONFIRM_TX` は補助スクリプトの実行条件であり、直接 CLI を使う例では指定しない。

#### コントラクトの初期化

コード登録時の TxHash を使って手順 5 の `check_tx` を実行し、結果の `events` から `code_id` を確認する。
取得した code ID を `CODE_ID` に設定し、初期化メッセージを使ってコントラクトを作成する。
以下では、コード登録用に設定したガス上限を、初期化・送金・ミントで使う設定例の `300000` に変更する。`source` は既存の `GAS` を保持するため、この変更を明示している。

```bash
GAS=300000
# WASM 登録の結果にある code_id を二重引用符の間に入力してから実行する。
CODE_ID=""
source scripts/CW20/load-env.sh
injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --label "cw20-mtk-sample" \
  --no-admin \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json \
  -y
```

初期化の TxHash で結果を確認し、`events` 内の `_contract_address` または `contract_address` の値を `CONTRACT_ADDR` に設定する。
`CODE_ID` は保存済みコードの番号、`CONTRACT_ADDR` は作成したコントラクトのアドレスであり、別の値である。

```bash
# 初期化の結果にあるコントラクトアドレスを二重引用符の間に入力してから実行する。
CONTRACT_ADDR=""
source scripts/CW20/load-env.sh
```

#### トークン情報と残高の照会

1つ目のコマンドで CW20 トークンの情報を、2つ目で自分のアドレス（`SENDER_ADDR`）の CW20 トークン残高を照会する。

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' \
  --node "$NODE" --output json | jq

injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' \
  --node "$NODE" --output json | jq
```

#### 送金

送金先と送金量を設定してから実行する。初期設定の宛先は自分のアドレスである。数量は最小単位で指定し、decimals が `6` の場合、`1000000` が `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="${RECIPIENT_ADDR:-$SENDER_ADDR}"
CW20_SEND_AMOUNT="1000000"
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json \
  -y
```

#### ミント

初期化時に設定した minter の鍵を `KEY_NAME` に指定し、環境変数を読み込む。その鍵で `CW20_MINT_AMOUNT` の数量を発行し、`SENDER_ADDR` に付与する。

```bash
source scripts/CW20/load-env.sh
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$SENDER_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json \
  -y
```

送金・ミント後も、返された TxHash で結果を確認する。

</details>
