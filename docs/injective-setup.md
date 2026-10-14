# injectived の導入・操作手順

本書は、Injective Testnet で使用する CLI `injectived` の導入、接続設定、鍵・ウォレットの管理、トランザクションの送信・確認を説明する。
共通の環境構築は、[メイン README](../README.md) を参照する。

本書のコマンドは、特に指定がない限り、Kali Linux のターミナルでリポジトリルートから実行する。パスは標準配置の例であり、作業先を変更した場合は読み替える。

```bash
cd ~/temp/sus_BC2
```

鍵名の既定値は `testwallet`、鍵の保存方式は `test` keyring backend である。環境変数を既に設定している場合、各 `load-env.sh` はその値を保持する。

## injectived の導入

一括セットアップの `SETUP_INJECTIVE` の既定値は `yes` で、標準設定では `injectived` の導入まで行う。Linux x86_64（amd64）向けの配布バイナリを使用するため、導入を有効にした一括セットアップは x86_64 を実行条件として確認する。
ARM などで CLI の導入を省略する場合は、次のように指定する。

```bash
SETUP_INJECTIVE=no ./setup/normal/wsl-kali-experiment-env.sh
```

この指定は CLI の導入処理を省略するもので、本書のウォレット・送金・TokenFactory・CW20 の操作には利用可能な `injectived` が必要である。
導入した CLI が起動できることは、次のコマンドで確認する。

```bash
injectived version
```

個別に導入する場合は、必要なパッケージをメイン README の `00-install-kali-packages.sh` で準備してから、[04-install-injectived.sh](../setup/normal/04-install-injectived.sh) を実行する。

<details>
<summary>補足：injectived の導入で実行するコマンド</summary>

`00-install-kali-packages.sh` で導入した `wget` と `unzip` を使い、Linux amd64 向けの配布ファイルを取得し、CLI と共有ライブラリを配置する。

```bash
mkdir -p ~/temp
cd ~/temp
wget -O linux-amd64.zip https://github.com/InjectiveFoundation/injective-core/releases/latest/download/linux-amd64.zip
unzip -o linux-amd64.zip
chmod +x injectived
sudo mv injectived /usr/local/bin/
if [ -f libwasmvm.x86_64.so ]; then
  sudo mv libwasmvm.x86_64.so /usr/lib/
  sudo ldconfig
fi
injectived version
cd ~/temp/sus_BC2
```

`wget -O` は保存するファイル名を指定してダウンロードし、`unzip -o` は既存ファイルを上書きして展開する。
`/usr/local/bin/` は CLI の配置先である。共有ライブラリが同梱されている場合は `/usr/lib/` に配置し、`ldconfig` でライブラリの検索情報を更新する。
最後に `injectived version` で起動できることを確認する。

手動で導入した場合は、最後にリポジトリルートへ戻り、以降の実験を行う。

</details>

<details>
<summary>補足：過去のバージョン確認記録</summary>

以下は過去の動作確認時の出力例である。配布ファイルは `latest` から取得するため、現在の導入結果は `injectived version` で確認する。

```text
Version v1.18.3 (b18483b)
Compiled at 20260331-2102 using Go go1.23.9 (amd64)
```

</details>

## ウォレットの作成・INJ の送金

ウォレットの作成と送金（`bank send`）には、次のスクリプトを使用する。

| 操作 | スクリプト |
| --- | --- |
| ウォレットの作成・確認 | [create-test-wallet.sh](../scripts/injectived/create-test-wallet.sh) |
| INJ の送金 | [bank-send.sh](../scripts/injectived/bank-send.sh) |

`injectived` 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

<details>
<summary>補足：環境変数の読み込みとウォレット作成のコマンド</summary>

#### 環境変数の設定

`load-env.sh` は `source` で読み込み、現在のシェルに `export` で値を設定する。
`${変数:-既定値}` は、変数が未設定または空の場合に既定値を使う指定である。すでに設定した値は保持される。
Injective 用の設定処理は次のとおりである。

```bash
export KEY_NAME="${KEY_NAME:-testwallet}"
export CHAIN_ID="${CHAIN_ID:-injective-888}"
export NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
export GAS_PRICES="${GAS_PRICES:-500000000inj}"
export GAS="${GAS:-1000000}"
export BANK_SEND_GAS="${BANK_SEND_GAS:-200000}"
export AMOUNT="${AMOUNT:-100000000inj}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if command -v injectived >/dev/null 2>&1; then
  export MY_ADDR="${MY_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export MY_ADDR="${MY_ADDR:-}"
fi
export ADDR="${ADDR:-$MY_ADDR}"
```

`KEY_NAME` は使用する鍵の名前、`CHAIN_ID` と `NODE` は接続先、`GAS_PRICES` はガス単価である。
`GAS` はガス上限、`BANK_SEND_GAS` は INJ 送金用のガス上限、`AMOUNT` は送金量、`RECIPIENT_ADDR` は送金先を表す。
`KEYRING_BACKEND` は鍵の保存方式を指定する。`keys show -a` は、鍵に対応するアドレスを取得する。
鍵がまだない場合、アドレスは空のままとなるため、作成後に取得する。

#### ウォレットの作成とアドレス取得

`create-test-wallet.sh` は、同じ名前の鍵が存在するか確認し、未作成の場合だけウォレットを作成する。

```bash
if ! injectived keys show "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" >/dev/null 2>&1; then
  injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
else
  echo "Wallet already exists: $KEY_NAME"
fi
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
```

作成済みの鍵を一覧で確認し、使用する鍵のアドレスを取得する場合は、次を実行する。

```bash
injectived keys list --keyring-backend "$KEYRING_BACKEND"
injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND"
```

`keys add` は鍵とウォレットを作成する。作成後の `MY_ADDR` を Faucet や残高照会に使用する。
この手動例では現在のシェルにアドレスが設定される。補助スクリプトを実行した場合は、表示される案内に従って環境変数を読み込む。

</details>

ウォレット作成後、[Injective testnet の Faucet](https://cloud.google.com/application/web3/faucet/injective/testnet) で INJ を取得し、残高を確認する。

```bash
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

送金時は `RECIPIENT_ADDR` と `AMOUNT` を設定し、`CONFIRM_SEND=yes` を指定して `bank-send.sh` を実行する。

<details>
<summary>補足：bank-send.sh が実行する送金コマンド</summary>

送信元の鍵、送金先、送金量を指定して、次のコマンドを実行する。例の送金先は実際のアドレスに置き換える。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
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

この応答はブロードキャスト時の記録であり、ブロックへの取り込み後の確定結果ではない。送金結果は、次の「トランザクションの確認」に従って別途確認する。

</details>

## トランザクションの確認

送金、TokenFactory、CW20 などの書き込み操作で TxHash が返ったら、次のコマンドで結果を確認する。
ブロックに取り込まれ、`code` が `0` であることを確認する。
`--broadcast-mode sync` の応答で `code: 0` と TxHash が返っても、`height: "0"` であれば確定成功を示すものではない。ブロックへの取り込み後、TxHash で結果を確認する。

```bash
TXHASH="ここにTxHashを入れる"
injectived q tx "$TXHASH" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --output json | jq
```

トランザクションは、次の Explorer でも確認できる。

- [Mintscan（Injective Testnet）](https://www.mintscan.io/injective-testnet)
- [Injective Testnet Explorer](https://testnet.explorer.injective.network/)

## injectived による TokenFactory / MTK の操作

TokenFactory を用いた MTK の作成、メタデータの設定、ミント（発行）、残高確認、送金には、[07-tokenfactory-mtk.sh](../setup/normal/07-tokenfactory-mtk.sh) を使用する。

TokenFactory 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

操作一覧は、次のコマンドで確認する。

```bash
./setup/normal/07-tokenfactory-mtk.sh help
```

`create-denom`、`set-metadata`、`mint`、`balance`、`send` の各操作を指定できる。
`create-denom` で denom を作成してから、メタデータ設定、ミント、送金へ進む。同じ denom の作成は一度だけ行う。
書き込み操作には `CONFIRM_TX=yes` と、作成手数料・ガス手数料を支払うための INJ 残高が必要である。
メタデータ設定の実行前に、補足の「メタデータの設定」に記載した CLI 引数の確認事項を参照する。

<details>
<summary>補足：TokenFactory の環境設定と各操作のコマンド</summary>

#### 環境変数と denom の組み立て

鍵名、チェーン、RPC、ガス単価、鍵の保存方式は Injective の共通設定と同じである。
TokenFactory 用の `load-env.sh` は、次の固有設定を読み込む。

```bash
export GAS="${GAS:-300000}"
export SUBDENOM="${SUBDENOM:-mtk}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
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
```

`CREATOR_ADDR` は作成者のアドレス、`SUBDENOM` はトークン名の末尾部分である。
完全な denom は `factory/作成者アドレス/subdenom` の形式になる。
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

`07-tokenfactory-mtk.sh env` は設定を画面に表示する操作であり、現在のシェルへの読み込みは `source` で行う。

#### denom の作成

`create-denom` では、subdenom、名称、記号、小数桁数を指定する。

```bash
injectived tx tokenfactory create-denom \
  "$SUBDENOM" "My Token" "MTK" 6 \
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

名称、説明、表示単位などを登録する。以下は現在のスクリプトが使う引数を示したものである。

```bash
injectived tx tokenfactory set-denom-metadata \
  "My Token Description" \
  "$DENOM" \
  "MTK" \
  "My Token" \
  "MTK" \
  "" \
  "" \
  "[{\"denom\":\"$DENOM\",\"exponent\":0,\"aliases\":[]},{\"denom\":\"MTK\",\"exponent\":6,\"aliases\":[]}]" \
  10 \
  6 \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

単位の JSON では、最小単位の exponent を `0`、表示単位 `MTK` の exponent を `6` としている。
現行スクリプトの末尾引数 `10 6` には、CLI の仕様との確認が必要である。
[公式の公開ソース v1.18.0](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) では、末尾2引数は `decimals` と `shouldDisableAdminBurn` である。
この仕様で `10 6` を渡すと、小数桁数は `10`、管理者の burn の無効化は `false`（文字列 `true` の場合だけ有効）として扱われ、作成時と単位 JSON の `6` 桁設定に一致しない。
[公式のトークン作成ガイド](https://docs.injective.network/developers-defi/token-launch) には9引数の例もあるため、実行前に導入した CLI の引数を次のコマンドで確認する。

```bash
injectived tx tokenfactory set-denom-metadata --help
```

上記のコードブロックは現在のスクリプト内容を示したものであり、引数の修正方針は使用する CLI の仕様に合わせて決める。

#### ミント・残高確認・送金

ミントは、数量と denom を連結し、発行先のアドレスを指定する。

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

送金は、宛先と最小単位の数量を設定してから実行する。小数桁数が `6` の場合、既定の `SEND_AMOUNT=1000000` は `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
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

## injectived による CW20 のコード登録・操作

登録する WASM ファイルの準備は、[メイン README の CW20 ビルドの補足](../README.md#cw20-サンプルの取得と-wasm-のビルド) を参照する。
生成された `~/temp/cw-plus/artifacts/cw20_base.wasm` をチェーンに登録するには、[11-store-cw20-code.sh](../setup/normal/11-store-cw20-code.sh) を使用する。

コードの登録には `CONFIRM_TX=yes` を指定する。登録用のガス設定例は `GAS=3000000` である。

CW20 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
```

初期化コマンドに渡す `instantiate_msg.json` は、[CW20 初期化メッセージの作成](cw20-instantiate-message.md) に従って準備する。

<details>
<summary>補足：CW20 の環境設定・コード登録・初期化・照会・送金・ミント</summary>

#### 環境変数とコード登録

CW20 用の `load-env.sh` は共通の鍵・接続設定に加え、次の保存先と操作用の変数を設定する。
`GAS` と同様に、`SENDER_ADDR`、`CODE_ID`、`CONTRACT_ADDR` などの既存値は保持される。鍵や対象コントラクトを変えた場合は、対応する値を設定し直してから読み込む。

```bash
export GAS="${GAS:-300000}"
export WORKDIR="${WORKDIR:-$HOME/temp}"
export CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"
export WASM_PATH="${WASM_PATH:-$CW_PLUS_DIR/artifacts/cw20_base.wasm}"
export CODE_ID="${CODE_ID:-}"
export CONTRACT_ADDR="${CONTRACT_ADDR:-}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export CW20_SEND_AMOUNT="${CW20_SEND_AMOUNT:-1000000}"
export CW20_MINT_AMOUNT="${CW20_MINT_AMOUNT:-1000000}"
if command -v injectived >/dev/null 2>&1; then
  export SENDER_ADDR="${SENDER_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export SENDER_ADDR="${SENDER_ADDR:-}"
fi
export MY_ADDR="${MY_ADDR:-$SENDER_ADDR}"
```

`WASM_PATH` はビルド済みコードの保存先である。
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

コード登録時の TxHash を使って「トランザクションの確認」のコマンドを実行し、結果の `events` から `code_id` を確認する。
取得した値を `CODE_ID` に設定し、初期化メッセージを使ってコントラクトを作成する。
以下では、コード登録用に設定したガス上限を、初期化・送金・ミントで使う設定例の `300000` に変更する。`source` は既存の `GAS` を保持するため、この変更を明示している。

```bash
GAS=300000
CODE_ID="取得したcode_id"
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
CONTRACT_ADDR="取得したcontract_address"
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

送金先と送金量を設定してから実行する。数量は最小単位で指定し、decimals が `6` の場合、`1000000` が `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
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

初期化時に設定した minter の鍵を `KEY_NAME` に指定し、環境変数を読み込んでから実行する。

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
