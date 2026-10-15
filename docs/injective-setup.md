# injectived の設定・操作手順

本書は、利用可能な CLI `injectived` がある環境を前提として、Injective Testnet への接続設定、鍵・ウォレットの管理、トランザクションの送信・確認を説明する。
共通の環境構築は、[メイン README](../README.md) を参照する。

本書のコマンドは、特に指定がない限り、Kali Linux のターミナルでリポジトリルートから実行する。パスは標準配置の例であり、作業先を変更した場合は読み替える。

以下は同じ Bash セッションで、番号順に実行する。最初の `bash` で Bash を起動する。初期設定では、送信元・受取先の両方に自分の `testwallet` を使用する。作成済みのウォレットを使う場合は、その鍵名を指定する。新しいウォレットを作る場合は、未使用の鍵名を指定する。
書き込み操作ごとに返された TxHash を照会し、ブロックへの取り込みと `code: 0` を確認してから次へ進む。Faucet での入金はブラウザで行う。手順 4 以降の TxHash・code ID・コントラクトアドレスは、コマンドの実行結果から自動で設定する。

## 1. 接続設定を読み込む

接続先と鍵名を明示し、前の実行のアドレス・識別子を引き継がないようにする。
まず次の1行だけを実行し、Bash のプロンプトが表示されてから、その下の設定ブロックを実行する。

```bash
bash
```

```bash
cd ~/temp/sus_BC2
export KEY_NAME="testwallet"
export KEYRING_BACKEND="test"
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
injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
export MY_ADDR
export ADDR="$MY_ADDR"
export RECIPIENT_ADDR="$MY_ADDR"
injectived keys list --keyring-backend "$KEYRING_BACKEND"
printf '送信元: %s\n受取先: %s\n' "$MY_ADDR" "$RECIPIENT_ADDR"
```

`MY_ADDR` と `ADDR` は自分のアドレス、`RECIPIENT_ADDR` は送金先である。初期設定では同じアドレスを使う。
作成された鍵を使って、後続の送金・トークン作成・コントラクト操作を行う。新しいターミナルを開いた場合は、手順 1・2 を実行し直す。

### 2.1. 受取アドレスを設定する

手順 2 が成功した同じ Bash セッションで実行する。初期設定の受取先は自分のアドレスである。別のアドレスへ送金する場合は、`inj1...` を実際の受取アドレスに置き換えて設定する。

```bash
export RECIPIENT_ADDR="inj1..."
```

後続の INJ・TokenFactory・CW20 の送金では、この `RECIPIENT_ADDR` を使う。

<details>
<summary>補足：環境変数の読み込みとウォレット作成のコマンド</summary>

#### 環境変数の設定

`load-env.sh` は `source` で読み込み、現在のシェルに `export` で値を設定する。すでに設定した値は保持される。
ウォレット作成後に、接続設定とアドレスを手動で設定する場合は次のように実行する。

```bash
export KEY_NAME="testwallet"
export KEYRING_BACKEND="test"
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

初期設定の宛先は自分の `MY_ADDR` である。この手順では別の宛先へ `0.001 INJ` を送金するため、`inj1...` を実際の受取アドレスに置き換えて `RECIPIENT_ADDR` に設定する。

```bash
export RECIPIENT_ADDR="inj1..."
```

設定した受取アドレスを確認する。

```bash
echo "RECIPIENT_ADDR=$RECIPIENT_ADDR"
```

続けて、対話シェルの設定を戻す。

```bash
set +e +u
set +o pipefail
```

同じ Bash で、必要なコマンドと取引関数の読み込みを確認する。この確認では送金しない。

```bash
cd ~/temp/sus_BC2
printf 'BASH_VERSION=%s\n' "${BASH_VERSION:-未設定}"
command -v jq injectived
source scripts/injectived/tx-utils.sh
declare -F run_tx wait_tx tx_event_value
```

`BASH_VERSION` にバージョン番号、`jq` と `injectived` の実行パス、3つの関数名が表示されることを確認する。`BASH_VERSION` が未設定の場合は手順 1 の `bash` を実行し、同じ確認をやり直す。エラーが表示された場合は送金へ進まない。

送金をやり直す前に、保存済みの TxHash と終了コードを確認する。このコマンドは値を表示するだけで、送金や変数の変更は行わない。

```bash
printf 'INJ_SEND_TX_HASH=%s\nTX_HASH=%s\nINJ_SEND_STATUS=%s\n' \
  "${INJ_SEND_TX_HASH:-未設定}" \
  "${TX_HASH:-未設定}" \
  "${INJ_SEND_STATUS:-未設定}"
```

`INJ_SEND_TX_HASH` が残っている場合は、再送する前に手順 5 で結果を確認する。`TX_HASH` だけが残っている場合は、今回の INJ 送金に対応する値か確認し、[確定待ちの再開手順](#送信後に確定待ちがタイムアウトした)で照会する。`TX_HASH` は別の取引の値である場合もある。
`未設定` は現在のシェルに値がないことを示し、未送信であることを保証しない。
JSON の解析に失敗した場合や送信済みか判断できない場合は、送金を繰り返さず、[応答ログの確認手順](#json-の解析に失敗した)へ進む。

受取アドレスと上記の確認結果に問題がなければ、送金する。

```bash
set +e +u
set +o pipefail
unset INJ_SEND_TX_HASH TX_HASH TX_RESULT
export AMOUNT="1000000000000000inj"
export BANK_SEND_GAS=200000
if source scripts/injectived/tx-utils.sh &&
   run_tx --hash-var INJ_SEND_TX_HASH env CONFIRM_SEND=yes bash ./scripts/injectived/bank-send.sh; then
  INJ_SEND_STATUS=0
  echo "INJ_SEND_TX_HASH=$INJ_SEND_TX_HASH"
else
  INJ_SEND_STATUS=$?
  printf '送金処理を中断しました（終了コード: %s）。表示されたエラーを確認し、次の手順には進まないでください。\n' "$INJ_SEND_STATUS" >&2
fi
```

`run_tx` が送金結果の TxHash を取得して確定成功を確認し、`INJ_SEND_TX_HASH` に自動で保存する。手順 5 ではこの値を使うため、TxHash の転記は不要である。失敗した場合はエラーと終了コードを表示してターミナルに戻る。`INJ_SEND_STATUS` は成功時に `0`、失敗時にその終了コードになる。
送信前にログ保存先が表示され、送信・照会の応答は JSON の解析前にファイルへ保存される。JSON の解析に失敗した場合も、[応答ログの確認手順](#json-の解析に失敗した)で確認できる。
送金処理でエラーが発生した場合は次へ進まない。確定待ちがタイムアウトした場合も同じ送金を繰り返さず、[確定待ちの再開手順](#送信後に確定待ちがタイムアウトした)で照会する。
この受取先の設定は後続の TokenFactory・CW20 の送金にも引き継がれる。

<details>
<summary>補足：送金コマンドと TxHash の自動取得</summary>

`bank-send.sh` は送信元の鍵、手順 4 で設定した受取アドレス、送金量を使って `injectived tx bank send` を実行する。補助スクリプトの代わりに直接 CLI を使う場合も、次のように `run_tx` で実行すると同じ変数に TxHash が保存される。

```bash
AMOUNT="1000000000000000inj"
BANK_SEND_GAS="${BANK_SEND_GAS:-${GAS:-200000}}"
run_tx --hash-var INJ_SEND_TX_HASH injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$BANK_SEND_GAS" \
  --output json \
  --broadcast-mode sync \
  -y
```

`--from` は署名に使う鍵、`--chain-id` と `--node` は接続先を指定する。
`--gas-prices` と `--gas` は手数料計算に使う設定である。送金には `BANK_SEND_GAS` を使う。
`--output json` は TxHash を自動取得できる形式で応答を出力する。`--broadcast-mode sync` は送信の受付結果を返し、その後 `run_tx` が TxHash を使ってブロックへの取り込みと成功を自動で確認する。
`-y` は CLI の確認を自動承認する指定である。
`CONFIRM_SEND=yes` は補助スクリプト内の実行条件であり、直接 `injectived` を実行する場合のオプションではない。
`inj` は INJ の最小単位で、`1000000000000000000inj` が `1 INJ` に相当する。この例の `1000000000000000inj` は `0.001 INJ` である。送金量は使用する `AMOUNT` の値で指定する。

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

この応答はブロードキャスト時の過去の記録であり、ブロックへの取り込み後の確定結果ではない。現行の手順 4 は `run_tx` で確定成功まで確認し、手順 5 でも保存済みの TxHash を使って結果を再確認する。

</details>

## 5. トランザクションの成功を確認する

手順 4 と同じ Bash セッションで、保存された `INJ_SEND_TX_HASH` を使って送金結果を再確認する。TxHash の手入力は不要である。`wait_tx` は照会だけを行い、送金は再実行しない。
ブロックへの取り込み後の `height` が正の整数、`code` が `0` である場合だけ成功とする。`--broadcast-mode sync` の受付応答で `code: 0` と TxHash が返っても、`height: "0"` は確定成功を示さない。

```bash
source scripts/injectived/tx-utils.sh
if [ -n "${INJ_SEND_TX_HASH:-}" ]; then
  wait_tx "$INJ_SEND_TX_HASH"
else
  echo "今回の INJ 送金の確定成功は確認できていません。手順 4 のエラーを確認してください。" >&2
fi
```

照会は既定で2秒間隔・最大30回行う。送信や確定確認に失敗した場合、手順 4 では古い `INJ_SEND_TX_HASH` を消去して停止するため、前回の送金結果を今回の結果として使わない。別の取引で `TX_HASH` が更新されても、この手順は INJ 送金専用の `INJ_SEND_TX_HASH` を使う。

トランザクションは、次の Explorer でも確認できる。

- [Mintscan（Injective Testnet）](https://www.mintscan.io/injective-testnet)
- [Injective Testnet Explorer](https://testnet.explorer.injective.network/)

## 6. TokenFactory で MTK を作成・送金する

手順 2 まで実行した同じ Bash セッションで、次の設定を読み込む。手順 6・7 では `run_tx` が送信結果から TxHash を取得し、確定結果の成功を確認してから次へ進む。コマンドが失敗した場合はエラーを確認し、次の操作へ進まない。対話中の Bash を自動終了させる設定は使用しない。

```bash
set +e +u
set +o pipefail
source scripts/injectived/tx-utils.sh
```

`TX_HASH` には直近の送信で取得した TxHash、`TX_RESULT` には成功が確認できた確定結果の JSON が入る。照会は既定で2秒間隔・最大30回行い、送信そのものは再試行しない。`run_tx --hash-var 変数名` は、その変数の前回値を消し、確定成功した場合だけ今回の TxHash を保存する。

| 操作 | 保存する環境変数 |
| --- | --- |
| INJ 送金 | `INJ_SEND_TX_HASH` |
| denom 作成 | `CREATE_DENOM_TX_HASH` |
| メタデータ設定 | `METADATA_TX_HASH` |
| TokenFactory のミント・送金 | `TOKENFACTORY_MINT_TX_HASH`・`TOKENFACTORY_SEND_TX_HASH` |
| WASM 登録・コントラクト初期化 | `STORE_TX_HASH`・`INSTANTIATE_TX_HASH` |
| CW20 の送金・ミント | `CW20_SEND_TX_HASH`・`CW20_MINT_TX_HASH` |

<details>
<summary>補足：TxHash・code ID・コントラクトアドレスの自動取得</summary>

[tx-utils.sh](../scripts/injectived/tx-utils.sh) の `run_tx` は、渡されたコマンドを1回実行し、`--output json` の応答から `txhash` を取得する。`--broadcast-mode sync` の受付結果だけで成功とせず、`wait_tx` が次の照会を繰り返して、ブロックへの取り込みを待つ。
操作別の TxHash は `--hash-var` で指定する。`run_tx` が失敗した後に、別行の `export STORE_TX_HASH="$TX_HASH"` などで保存しない。

```bash
injectived q tx "$TX_HASH" \
  --chain-id="$CHAIN_ID" --node="$NODE" --output json
```

照会結果の TxHash が送信時の値と一致し、`height` が正の整数、`code` が `0` である場合だけ、確定結果を `TX_RESULT` に保存する。送信・照会の JSON が不正な場合や、確定結果が失敗の場合は停止し、以前の成功結果を再利用しない。
`TX_MAX_ATTEMPTS`（正の整数、既定 `30`）と `TX_RETRY_DELAY`（秒、非負整数、既定 `2`）で、照会回数と間隔を指定できる。待機上限に達した場合は表示された TxHash を確認し、同じ送信コマンドを繰り返さず、照会で結果を確認する。

`tx_event_value` は `TX_RESULT` のイベントから、指定した項目を取り出す。CLI の通常形式と `tx_response` で包まれた形式、`events` と `logs[].events` の両方を扱う。

```bash
CODE_ID="$(tx_event_value store_code code_id)"
CONTRACT_ADDR="$(tx_event_value instantiate _contract_address contract_address)"
```

上の2行は、それぞれ WASM 登録・初期化の成功直後に実行する。`TX_RESULT` は次の書き込み操作で更新されるため、手順 7.2・7.5 の順序に従う。対象項目が見つからない場合や、異なる値が複数ある場合は停止する。同じ値が複数のイベントに含まれる場合は1つにまとめる。

</details>

<details>
<summary>補足：送信・照会の応答ログ</summary>

`run_tx` は送信前に固有のログディレクトリを作り、そのパスを画面に表示するとともに `TX_LOG_DIR` に保存する。標準の保存先は `~/.local/state/sus_BC2/transactions/` 以下で、`XDG_STATE_HOME` が設定されている場合はそのディレクトリ以下になる。親ディレクトリは `TX_LOG_ROOT` でも変更できる。

| ファイル | 内容 |
| --- | --- |
| `submission.stdout` | 送信コマンドの標準出力（未加工の応答） |
| `submission.stderr` | 送信コマンドの標準エラー出力 |
| `submission.status` | 送信コマンドの終了コード |
| `query-1.stdout`・`query-1.stderr`・`query-1.status` | 1回目の照会の標準出力・標準エラー出力・終了コード |
| `query-2.*` 以降 | 2回目以降の照会の記録 |

送信とその確定照会は同じディレクトリに記録する。`wait_tx` を単独で呼び出した場合は新しいディレクトリを作成し、`TX_LOG_DIR` を更新して照会だけを記録する。元のログは削除・上書きしない。
各ディレクトリの権限は `700`、各ファイルは `600` とし、実行ユーザーだけが読み書きできる。ログの準備に失敗した場合は送信を開始しない。JSON が不正な場合やコマンドが失敗した場合も応答を残し、送信を自動で再試行しない。

`submission.status` の `0` はコマンドの正常終了を示すだけで、チェーン上の確定成功を保証しない。`jq` の解析エラーも未送信を意味しない。確認方法は[JSON の解析に失敗した場合の手順](#json-の解析に失敗した)を参照する。

</details>

### 6.1. 設定を読み込み、denom を作成する

同じ鍵・subdenom の組み合わせでの作成は一度だけ行う。作成済みなら作成コマンドを省略するか、`SUBDENOM` を未使用の名前に変更する。

```bash
export GAS=300000
export SUBDENOM="mtk"
export CREATOR_ADDR="$MY_ADDR"
export DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
source scripts/tokenfactory/load-env.sh
```

`DENOM` は自分のアドレスと `SUBDENOM` から自動で組み立てる。作成済みの denom を使う場合も上の設定は実行し、次の作成ブロックだけを省略する。

```bash
run_tx --hash-var CREATE_DENOM_TX_HASH env CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh create-denom
```

### 6.2. メタデータを設定する

`set-metadata` は、使用中の CLI の Usage を確認して、小数桁数 `6` に合う末尾引数を選ぶ。
[公式 v1.18.0 の CLI](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) は末尾に `[decimals] [shouldDisableAdminBurn]` を取り、[公式ガイド](https://docs.injective.network/developers-defi/token-launch) は `[decimals]` のみの例を掲載している。補助スクリプトは `6 false` または `6` を渡し、どちらにも一致しない場合やヘルプ取得に失敗した場合は送信せず停止する。

```bash
run_tx --hash-var METADATA_TX_HASH env CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh set-metadata
```

<details>
<summary>補足：メタデータ設定を CLI で直接実行する場合</summary>

補助スクリプトの代わりに次の関数を実行できる。補助スクリプトと同じ判定で引数を選ぶ。

```bash
set_token_metadata() {
  local metadata_help
  local metadata_args
  metadata_help="$(injectived tx tokenfactory set-denom-metadata --help)" || return
  printf '%s\n' "$metadata_help" >&2
  if grep -Fq '[shouldDisableAdminBurn]' <<< "$metadata_help"; then
    metadata_args=(6 false)
  elif grep -Eq 'set-denom-metadata .*\[decimals\]([[:space:]]+\[flags\])?[[:space:]]*$' <<< "$metadata_help"; then
    metadata_args=(6)
  else
    echo "Usage の位置引数を確認してからメタデータを設定してください。" >&2
    return 1
  fi
  injectived tx tokenfactory set-denom-metadata \
    "My Token Description" "$DENOM" "MTK" "My Token" "MTK" "" "" \
    "[{\"denom\":\"$DENOM\",\"exponent\":0,\"aliases\":[]},{\"denom\":\"MTK\",\"exponent\":6,\"aliases\":[]}]" \
    "${metadata_args[@]}" \
    --from="$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
    --chain-id="$CHAIN_ID" --node="$NODE" \
    --gas-prices="$GAS_PRICES" --gas="$GAS" \
    --output json --broadcast-mode sync -y
}
run_tx --hash-var METADATA_TX_HASH set_token_metadata
```

</details>

### 6.3. MTK をミントする

小数桁数 `6` の場合、`1000000000` は `1000 MTK` に相当する。

```bash
run_tx --hash-var TOKENFACTORY_MINT_TX_HASH env MINT_AMOUNT=1000000000 CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh mint
```

### 6.4. 残高を確認する

```bash
bash ./setup/normal/07-tokenfactory-mtk.sh balance
```

### 6.5. MTK を送金し、受取先の残高を確認する

宛先は `RECIPIENT_ADDR` を使う。手順 4 で別の受取アドレスを設定した場合は、その宛先へ送金する。

```bash
export SEND_AMOUNT=1000000
run_tx --hash-var TOKENFACTORY_SEND_TX_HASH env CONFIRM_TX=yes bash ./setup/normal/07-tokenfactory-mtk.sh send
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
run_tx --hash-var CREATE_DENOM_TX_HASH injectived tx tokenfactory create-denom \
  "$SUBDENOM" "My Token" "MTK" 6 \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json --broadcast-mode sync \
  -y
```

作成トランザクションの成功を確認してから、以降の操作へ進む。

#### メタデータの設定

名称、説明、表示単位などを登録する。実行には手順 6.2 の `set-metadata` または CLI の直接実行例を使用する。

単位の JSON では、最小単位の exponent を `0`、表示単位 `MTK` の exponent を `6` としている。
[公式の公開ソース v1.18.0](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) では、末尾2引数は `decimals` と `shouldDisableAdminBurn` である。
この仕様では末尾に `6 false` を渡し、小数桁数を `6`、管理者の burn の無効化を `false` とする。
[公式のトークン作成ガイド](https://docs.injective.network/developers-defi/token-launch) の9引数の例では、末尾に `6` のみを渡す。補助スクリプトは、次のコマンドの Usage を確認して引数を切り替える。

```bash
injectived tx tokenfactory set-denom-metadata --help
```

Usage に想定した末尾引数が見つからない場合は送信せず停止する。小数桁数と単位 JSON の exponent は、作成時の `6` 桁設定にそろえている。

#### ミント・残高確認・送金

ミントは、数量と denom を連結し、発行先のアドレスを指定する。

```bash
MINT_AMOUNT="${MINT_AMOUNT:-1000000000}"
run_tx --hash-var TOKENFACTORY_MINT_TX_HASH injectived tx tokenfactory mint "${MINT_AMOUNT}${DENOM}" "$CREATOR_ADDR" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json --broadcast-mode sync \
  -y
```

`MINT_AMOUNT` は最小単位の数量で、変数自体には denom を含めない。
小数桁数が `6` の場合、既定の `1000000000` は `1000 MTK` に相当する。
次のコマンドは、作成者の銀行残高を JSON で取得する。

```bash
injectived query bank balances "$CREATOR_ADDR" \
  --node="$NODE" --chain-id="$CHAIN_ID" -o json | jq
```

送金は、現在の `RECIPIENT_ADDR` と最小単位の数量を使って実行する。手順 4 で別の宛先を設定した場合は、その設定を引き継ぐ。小数桁数が `6` の場合、既定の `SEND_AMOUNT=1000000` は `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="${RECIPIENT_ADDR:-$CREATOR_ADDR}"
SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
run_tx --hash-var TOKENFACTORY_SEND_TX_HASH injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "${SEND_AMOUNT}${DENOM}" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json --broadcast-mode sync \
  -y
```

`CONFIRM_TX=yes` は補助スクリプト側の実行条件である。直接 CLI を使う場合は、上記のコマンドで処理を実行する。
各書き込み操作の結果は `run_tx` が自動で照会し、確定結果の成功を確認する。

</details>

## 7. CW20 のコード登録・初期化・送金・ミントを行う

登録する WASM ファイルは、[メイン README の CW20 ビルドの補足](../README.md#cw20-サンプルの取得と-wasm-のビルド) に従って準備しておく。
手順 1・2 で設定した同じ Bash セッションで実行する。新しいターミナルの場合は、手順 1 と手順 2 のアドレス取得を実行し直す。ウォレットが作成済みの場合、`keys add` は省略する。
TokenFactory の手順 6 を省略しても、CW20 の `load-env.sh` が `run_tx`・`wait_tx`・`tx_event_value` を読み込む。`bash scripts/CW20/load-env.sh` ではなく、次の例のように `source` で読み込む。

### 7.1. 設定を読み込み、WASM を登録する

```bash
set +e +u
set +o pipefail
unset STORE_TX_HASH TX_HASH TX_RESULT CODE_ID CONTRACT_ADDR
export GAS=3000000
source scripts/CW20/load-env.sh &&
export SENDER_ADDR="$MY_ADDR" &&
export CREATOR_ADDR="$MY_ADDR" &&
declare -F run_tx wait_tx tx_event_value &&
printf '署名者: %s\nWASM: %s\n' "$SENDER_ADDR" "$WASM_PATH" &&
run_tx --hash-var STORE_TX_HASH env CONFIRM_TX=yes bash ./setup/normal/11-store-cw20-code.sh
```

### 7.2. 登録結果を確認し、code ID を設定する

直前の WASM 登録の確定結果から `code_id` を取得する。画面からの転記は不要である。

```bash
CODE_ID="$(tx_event_value store_code code_id)" &&
[[ "$CODE_ID" =~ ^[1-9][0-9]*$ ]] &&
export CODE_ID &&
printf 'CODE_ID=%s\n' "$CODE_ID"
```

### 7.3. 初期化メッセージを作成する

```bash
TOKEN_NAME="My Token" TOKEN_SYMBOL="MTK" TOKEN_DECIMALS=6 INITIAL_BALANCE=1000000 OUTPUT_FILE=instantiate_msg.json \
  bash ./scripts/CW20/create-instantiate-msg.sh
jq . instantiate_msg.json
```

JSON の初期残高と minter のアドレスが `CREATOR_ADDR` と一致することを確認する。生成処理の詳細は、[CW20 初期化メッセージの作成](cw20-instantiate-message.md) を参照する。

### 7.4. コントラクトを初期化する

コード登録用のガス値から、以降の操作の値へ切り替える。

```bash
export GAS=300000
run_tx --hash-var INSTANTIATE_TX_HASH injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" --node="$NODE" \
  --label "cw20-mtk-sample" --no-admin \
  --gas-prices="$GAS_PRICES" --gas="$GAS" --output json --broadcast-mode sync -y
```

### 7.5. コントラクトアドレスを設定する

直前の初期化の確定結果から `_contract_address` または `contract_address` を取得する。

```bash
CONTRACT_ADDR="$(tx_event_value instantiate _contract_address contract_address)" &&
export CONTRACT_ADDR &&
printf 'CONTRACT_ADDR=%s\n' "$CONTRACT_ADDR"
```

### 7.6. トークン情報と残高を確認する

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' --node "$NODE" --output json | jq
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' --node "$NODE" --output json | jq
```

### 7.7. CW20 トークンを送金する

宛先は `RECIPIENT_ADDR` を使う。手順 4 で別の受取アドレスを設定した場合は、その宛先へ送金する。

```bash
export CW20_SEND_AMOUNT=1000000
run_tx --hash-var CW20_SEND_TX_HASH injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" --node "$NODE" \
  --gas-prices "$GAS_PRICES" --gas "$GAS" --output json --broadcast-mode sync -y
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$RECIPIENT_ADDR"'"}}' --node "$NODE" --output json | jq
```

### 7.8. CW20 トークンをミントする

初期化メッセージで minter に設定した `KEY_NAME` の鍵で実行する。

```bash
export CW20_MINT_AMOUNT=1000000
run_tx --hash-var CW20_MINT_TX_HASH injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$SENDER_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" --node "$NODE" \
  --gas-prices "$GAS_PRICES" --gas "$GAS" --output json --broadcast-mode sync -y
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' --node "$NODE" --output json | jq
```

<details>
<summary>補足：CW20 の環境設定・コード登録・初期化・照会・送金・ミント</summary>

#### 環境変数とコード登録

CW20 用の `load-env.sh` は共通の鍵・接続設定に加え、次の保存先と操作用の変数を設定する。
`GAS` と同様に、`SENDER_ADDR`、`CODE_ID`、`CONTRACT_ADDR` などの既存値は保持される。鍵や対象コントラクトを変えた場合は、対応する値を設定し直してから読み込む。
同じ Bash に共通の取引関数も読み込む。取引関数の読み込みでは送信や既存の `TX_HASH`・`TX_RESULT` の消去は行わない。

```bash
source scripts/injectived/tx-utils.sh
```

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
run_tx --hash-var STORE_TX_HASH injectived tx wasm store "$WASM_PATH" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json --broadcast-mode sync -y
```

`store` は WASM コードをチェーンへ登録する操作で、成功後に code ID を取得できる。
補助スクリプトも `--output json --broadcast-mode sync -y` を指定し、`run_tx` が応答を読み取れる形式で送信する。
`CONFIRM_TX` は補助スクリプトの実行条件であり、直接 CLI を使う例では指定しない。

#### コントラクトの初期化

コード登録を `run_tx` で実行した直後の `TX_RESULT` から、`store_code` イベントの `code_id` を自動で取り出す。
その値を `CODE_ID` に設定し、初期化メッセージを使ってコントラクトを作成する。
以下では、コード登録用に設定したガス上限を、初期化・送金・ミントで使う設定例の `300000` に変更する。`source` は既存の `GAS` を保持するため、この変更を明示している。

```bash
GAS=300000
CODE_ID="$(tx_event_value store_code code_id)"
[[ "$CODE_ID" =~ ^[1-9][0-9]*$ ]]
export CODE_ID
source scripts/CW20/load-env.sh
run_tx --hash-var INSTANTIATE_TX_HASH injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --label "cw20-mtk-sample" \
  --no-admin \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json --broadcast-mode sync \
  -y
```

初期化の確定結果から、`instantiate` イベントの `_contract_address` または `contract_address` を `CONTRACT_ADDR` に設定する。
`CODE_ID` は保存済みコードの番号、`CONTRACT_ADDR` は作成したコントラクトのアドレスであり、別の値である。

```bash
CONTRACT_ADDR="$(tx_event_value instantiate _contract_address contract_address)"
export CONTRACT_ADDR
source scripts/CW20/load-env.sh
```

#### トークン情報と残高の照会

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' \
  --node "$NODE" --output json | jq

injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' \
  --node "$NODE" --output json | jq
```

#### 送金

送金には現在の `RECIPIENT_ADDR` を使い、手順 4 で設定した宛先を引き継ぐ。数量は最小単位で指定し、decimals が `6` の場合、`1000000` が `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="${RECIPIENT_ADDR:-$SENDER_ADDR}"
CW20_SEND_AMOUNT="1000000"
run_tx --hash-var CW20_SEND_TX_HASH injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json --broadcast-mode sync \
  -y
```

#### ミント

初期化時に設定した minter の鍵を `KEY_NAME` に指定し、環境変数を読み込んでから実行する。

```bash
source scripts/CW20/load-env.sh
run_tx --hash-var CW20_MINT_TX_HASH injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$SENDER_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json --broadcast-mode sync \
  -y
```

送金・ミント後も `run_tx` が確定結果の成功を確認する。TxHash はそれぞれ `CW20_SEND_TX_HASH`・`CW20_MINT_TX_HASH` に保存される。

</details>

## 困ったとき

### コマンドを貼り付けるとターミナルが閉じる

対話中の Bash で `set -e` を有効にすると、コマンドの失敗で Bash が終了する場合がある。ターミナルの設定によっては、そのままウィンドウも閉じる。この手順では対話シェルに `set -euo pipefail` を設定せず、操作の失敗と終了コードを表示する。個別のシェルスクリプト内の設定は、その子プロセスだけに適用される。

ターミナルを開き直したら、まず Bash で次を実行して対話シェルの設定を戻す。この操作では送金しない。

```bash
set +e +u
set +o pipefail
```

エラーが残っていない場合は、次の送金を実行する前に、読み取りだけの診断を行う。出力は画面と `~/sus-bc2-shell-diagnostics.log` に残す。
まず[手順 4 の確認コマンド](#4-injを送金する)で、Bash のバージョン、必要なコマンド、取引関数の読み込みを確認する。

```bash
cd ~/temp/sus_BC2
{
  printf 'BASH_VERSION=%s\nshell flags=%s\n' "${BASH_VERSION:-未設定}" "$-"
  command -v bash jq injectived
  git log -1 --oneline
  bash -n scripts/injectived/tx-utils.sh
  bash -n scripts/injectived/bank-send.sh
} 2>&1 | tee -a "$HOME/sus-bc2-shell-diagnostics.log"
```

これは取引を送信せず、鍵も作成・変更しない。閉じる直前の操作が送信済みか不明な場合は、送金ブロックを繰り返さず、表示・記録された今回の TxHash を照会する。
保存済みの値が残っているかは、[手順 4 の TxHash 確認コマンド](#4-injを送金する)で確認する。変数を消したり送金をやり直したりする前に実行する。
WSL 自体が停止したかは、この症状だけでは判断できない。Windows の PowerShell で次を実行すると、ディストリビューションの状態を確認できる（[Microsoft のコマンド一覧](https://learn.microsoft.com/en-us/windows/wsl/basic-commands#list-installed-linux-distributions)）。

```powershell
wsl --list --verbose
```

### `run_tx: command not found` と表示される

`run_tx` は `injectived` のサブコマンドではなく、[tx-utils.sh](../scripts/injectived/tx-utils.sh) が現在の Bash に定義する関数である。別のターミナルを開いた場合や、取引関数を読み込む前に操作した場合は未定義になる。
CW20 の `load-env.sh` はこの関数も読み込む。修正前のファイルを使っている場合でも、共通の補助ファイルを明示的に `source` すれば読み込める。

まず Bash で手順 1 の接続設定と、手順 2 の既存ウォレットのアドレス取得を行い、次を実行する。ウォレットの作り直しは不要である。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/tx-utils.sh
declare -F run_tx wait_tx tx_event_value
```

この3つの関数名が表示されることを確認する。上のコマンドは取引を送信しない。

`run_tx: command not found` で失敗した行では、その引数に指定した WASM 登録スクリプトは実行されていない。その直後に `export STORE_TX_HASH="$TX_HASH"` を実行しても、今回の登録結果にはならない。今回のエラーだけが発生し、ほかに登録を送信していない場合は、前回の値を消してから手順 7.1 を1回実行する。

```bash
unset STORE_TX_HASH TX_HASH TX_RESULT CODE_ID CONTRACT_ADDR
```

別の試行で TxHash が返っている場合は、値を消したり登録を再送したりする前に、次の確定待ちの手順でその取引を確認する。

### JSON の解析に失敗した

`jq: parse error` や `Invalid transaction submission JSON.` は、受け取った応答を JSON として解析できなかったことを示す。送信後にこのエラーが発生する場合があるため、送信済みかどうかはこのエラーだけでは判断できない。ログ取得のために送金・WASM 登録・初期化を再実行しない。

同じ Bash で、今回のログ保存先を確認する。

```bash
printf 'TX_LOG_DIR=%s\n' "${TX_LOG_DIR:-未設定}"
```

`TX_LOG_DIR` が今回の送信ログを指していることを確認してから、終了コードと生の応答を表示する。この操作はファイルの読み取りだけを行う。

```bash
if [ -n "${TX_LOG_DIR:-}" ] && [ -f "$TX_LOG_DIR/submission.stdout" ]; then
  RECOVERY_LOG_DIR="$TX_LOG_DIR"
  printf '\n--- 送信コマンドの終了コード ---\n'
  cat -- "$RECOVERY_LOG_DIR/submission.status"
  printf '\n--- 標準出力 ---\n'
  cat -- "$RECOVERY_LOG_DIR/submission.stdout"
  printf '\n--- 標準エラー出力 ---\n'
  cat -- "$RECOVERY_LOG_DIR/submission.stderr"
else
  echo "今回の送信ログの保存先を、実行時に表示されたパスから確認してください。" >&2
fi
```

Bash を開き直した場合や、その後の `wait_tx` で `TX_LOG_DIR` が更新された場合は、実行時に表示された今回の送信ログのパスを設定してから上の確認を行う。

```bash
export TX_LOG_DIR="実行時に表示された今回の送信ログの絶対パス"
```

表示されたパスが分からない場合は、保存先のディレクトリを更新日時順に一覧表示し、実行時刻に対応するものを確認する。一覧の先頭が今回の送信とは限らず、照会だけのログも含まれる。

```bash
ls -lt -- "${TX_LOG_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/sus_BC2/transactions}"
```

JSON ではなく YAML が返っている場合や、応答の前後に別のメッセージが混ざっている場合も、元の出力は `submission.stdout` に残る。`submission.status` が `0` でも解析に失敗した場合は、確定成功として扱わず、`INJ_SEND_TX_HASH` などの操作別変数には保存しない。

ログの `txhash` に今回の取引の64桁のハッシュが見つかった場合は、その値を次の `RECOVERY_TX_HASH` に設定して照会する。送信元・宛先・金額・実行時刻も照合し、別の取引のハッシュを使わない。

```bash
RECOVERY_TX_HASH="今回の取引の64桁のTxHash"
source scripts/injectived/tx-utils.sh
wait_tx "$RECOVERY_TX_HASH"
```

このコマンドは照会だけを行う。`wait_tx` はハッシュの一致、正の `height`、`code` が `0` であることを確認してから `TX_RESULT` に保存する。確定成功を確認できた INJ 送金は手順 6、WASM 登録は手順 7.2、コントラクト初期化は手順 7.5 から再開する。
照会応答の JSON 解析に失敗した場合は、表示されたログディレクトリの `query-1.stdout`・`query-1.stderr`・`query-1.status` 以降を確認する。`wait_tx` を再実行しても送信は行わない。

TxHash が見つからない場合は、手順 5 の Explorer で送信元アドレスの取引履歴を開き、実行時刻・宛先・金額が対応する取引を探す。取引を見つけられない場合も、未送信と決めつけて再送しない。修正前のスクリプトが保存しなかった応答は、この変更では復元できないため、その場合も取引履歴から確認する。

### 送信後に確定待ちがタイムアウトした

タイムアウトは送信の失敗を意味しない。送信コマンドを再実行せず、今回の TxHash への照会だけを再開する。
同じ Bash に今回の `TX_HASH` が残っている場合は、次を実行する。

```bash
source scripts/injectived/tx-utils.sh
wait_tx "$TX_HASH"
```

Bash を開き直した場合は接続設定を読み込み、タイムアウト時に表示された今回の TxHash を `wait_tx` の引数に指定する。古い `STORE_TX_HASH` や別の取引の TxHash を流用しない。
INJ 送金の確定成功が確認できた場合は、その照会で手順 5 の確認も完了するため、手順 6 へ進む。タイムアウト時には `INJ_SEND_TX_HASH` が未設定なので、手順 5 をそのまま再実行しない。
WASM 登録後は手順 7.2、コントラクト初期化後は手順 7.5 から再開する。`wait_tx` の照会には手数料はかからず、送金・WASM 登録・初期化を再送しない。
