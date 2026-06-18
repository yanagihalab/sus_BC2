# CW20 README

## CW20 コントラクト用の Docker / CosmWasm 環境構築

CW20 コントラクトをビルドするためには、CosmWasm コントラクトを WASM 形式へ変換するビルド環境が必要である。
本実験では、ホスト環境に Rust / Cargo の詳細なビルド環境を直接構築せず、`cosmwasm/workspace-optimizer` Docker イメージを用いて最適化済み WASM を生成する。

また、本実験では、CosmWasm の `cw-plus` に含まれる `cw20-base` をサンプルコードとして利用する。
`cw20-base` は、CW20 トークンの基本実装であり、トークン名、シンボル、初期残高、mint 権限などを設定して利用できる。

### Docker Engine の導入

`cosmwasm/workspace-optimizer` を利用するためには、Docker Engine が必要である。
Docker Engine の導入コマンドを以下に示す。

```bash
cd ~/temp/sus_BC2
sudo apt update
sudo apt install -y docker.io
sudo service docker start
sudo docker --version
```

対応する setup script: `./setup/normal/09-install-docker.sh`

一般ユーザで Docker を実行する場合は、必要に応じて現在のユーザを `docker` グループに追加する。
Docker グループへの追加コマンドを以下に示す。

```bash
cd ~/temp/sus_BC2
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
```

対応する setup script: `ADD_USER_TO_DOCKER_GROUP=yes RUN_HELLO_WORLD=yes ./setup/normal/09-install-docker.sh`

### CW20 サンプルコードの取得

本実験では、CW20 コントラクトを一から実装するのではなく、CosmWasm が提供する `cw-plus` リポジトリ内の `cw20-base` をサンプルコードとして利用する。

`cw-plus` の取得コマンドを以下に示す。

```bash
cd ~/temp
git clone https://github.com/CosmWasm/cw-plus.git
cd cw-plus
ls
```

対応する setup script: `./setup/normal/10-build-cw20-sample.sh`

`cw20-base` コントラクトは、`cw-plus/contracts/cw20-base` に含まれている。
確認コマンドを以下に示す。

```bash
cd ~/temp/cw-plus
ls contracts/cw20-base
```

対応する setup script: `./setup/normal/10-build-cw20-sample.sh`

### workspace-optimizer によるビルド

取得した `cw20-base` コントラクトを WASM 形式へビルドする。
本実験では、`cosmwasm/workspace-optimizer` を用いて Docker 上で最適化ビルドを行う。

`cosmwasm/workspace-optimizer` は、CosmWasm コントラクトを再現性のある環境でビルドし、WASM サイズの最適化を行うための Docker イメージである。
特に、`cw-plus` のように複数のコントラクトを含む workspace 形式のリポジトリをビルドする場合に適している。

`workspace-optimizer` を用いる場合は、`contracts/cw20-base` ディレクトリではなく、`cw-plus` のルートディレクトリで実行する点に注意する。
ビルドコマンドを以下に示す。

```bash
cd ~/temp/cw-plus

docker run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0
```

対応する setup script: `./setup/normal/10-build-cw20-sample.sh`

ビルドが成功すると、`artifacts` ディレクトリに最適化済みの WASM ファイルが出力される。
`cw20-base` の場合は、通常、`artifacts/cw20_base.wasm` が生成される。

生成物の確認コマンドを以下に示す。

```bash
cd ~/temp/cw-plus
ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
```

対応する setup script: `./setup/normal/10-build-cw20-sample.sh`

### コントラクトコードの保存

次に、ビルド済みの WASM ファイルを Injective チェーンへ保存する。
`workspace-optimizer` によって生成された `artifacts/cw20_base.wasm` を指定する。

保存コマンド例を以下に示す。

```bash
cd ~/temp/cw-plus
injectived tx wasm store artifacts/cw20_base.wasm \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas=3000000
```

対応する setup script: `CONFIRM_TX=yes ./setup/normal/11-store-cw20-code.sh`

保存に成功すると、トランザクション結果から code ID を確認できる。
以降のインスタンス化では、この code ID を指定する。

### CW20 code ID を確認する

`store` の実行後に `txhash` が返ったら、次のコマンドで code ID を確認する。

```bash
cd ~/temp/sus_BC2
TXHASH="ここにTxHashを入れる"

injectived q tx "$TXHASH" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --output json | jq
```

対応する setup script: なし。TxHash ごとに個別確認するコマンドである。

出力の `events` から `code_id` を確認し、環境変数に入れる。

```bash
cd ~/temp/sus_BC2
CODE_ID="取得したcode_id"
source scripts/CW20/load-env.sh
```

対応する shell script: `source scripts/CW20/load-env.sh`

### CW20 コントラクトをインスタンス化する

`cw20-base` を利用するには、保存した code ID からコントラクトをインスタンス化する。
ここでは、`testwallet` のアドレスに初期残高と mint 権限を与える。
CW20 の `symbol` は、英字またはハイフンのみで、3 文字以上 12 文字以下である必要がある。

使用できない `symbol` の例を以下に示す。

```text
factory/inj1.../mtk
mtk_v2
MTK1
MT
My Token
```

使用できる `symbol` の例を以下に示す。

```text
MTK
MYTOKEN
MTK-TOKEN
TESTTOKEN
```

`name` は表示名であるため、空白を含めてもよい。

まず、`instantiate_msg.json` がある場合は内容を確認する。

```bash
cd ~/temp/sus_BC2
cat instantiate_msg.json | jq
cat instantiate_msg.json | jq -r '.symbol'
```

対応する setup script: なし。instantiate message の内容を個別確認するコマンドである。

`symbol` が `factory/.../mtk` や `mtk_v2` のような値になっている場合は、次の内容で `instantiate_msg.json` を作り直す。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
scripts/CW20/create-instantiate-msg.sh
```

対応する shell script: `source scripts/CW20/load-env.sh`、`scripts/CW20/create-instantiate-msg.sh`

`symbol` の形式だけを確認する場合は、次のコマンドを実行する。

```bash
cd ~/temp/sus_BC2
SYMBOL=$(jq -r '.symbol' instantiate_msg.json)

echo "SYMBOL=$SYMBOL"

echo "$SYMBOL" | grep -Eq '^[A-Za-z-]{3,12}$' \
  && echo "[OK] symbol format is valid" \
  || echo "[NG] symbol format is invalid"
```

対応する setup script: なし。CW20 symbol の形式を個別確認するコマンドである。

`CODE_ID` が分かっている場合は、先に設定する。

```bash
cd ~/temp/sus_BC2
CODE_ID="ここにcode_idを入れる"
source scripts/CW20/load-env.sh
```

対応する shell script: `source scripts/CW20/load-env.sh`

インスタンス化を実行する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh

INSTANTIATE_TXHASH=$(injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --label "cw20-mtk-sample" \
  --no-admin \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json \
  -y | tee instantiate_tx.json | jq -r '.txhash')

echo "INSTANTIATE_TXHASH=$INSTANTIATE_TXHASH"
```

対応する setup script: なし。CW20 の instantiate は code ID と初期化内容に依存するため、個別に実行する。

`1000000` は decimals が `6` の場合、`1 MTK` に相当する。
TokenFactory の denom は `factory/inj.../mtk` の形式でよいが、CW20 の `symbol` には使えない。
CW20 の `symbol` は表示用の短い ticker であるため、`"symbol": "MTK"` のように指定する。

### CW20 contract address を確認する

インスタンス化の TxHash が返ったら、Tx 結果を確認する。

```bash
cd ~/temp/sus_BC2
sleep 6

injectived q tx "$INSTANTIATE_TXHASH" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --output json | tee instantiate_result.json | jq '{height:.height, code:.code, raw_log:.raw_log, txhash:.txhash}'
```

対応する setup script: なし。TxHash ごとに個別確認するコマンドである。

出力の `events` から `_contract_address` を確認し、環境変数に入れる。

```bash
cd ~/temp/sus_BC2
CONTRACT_ADDR=$(jq -r '
  [
    (.logs // .tx_response.logs // [])[].events[]?
    | select(.type == "instantiate")
    | .attributes[]?
    | select(.key == "_contract_address" or .key == "contract_address")
    | .value
  ][0]
' instantiate_result.json)
source scripts/CW20/load-env.sh

echo "CONTRACT_ADDR=$CONTRACT_ADDR"

if [ -z "$CONTRACT_ADDR" ] || [ "$CONTRACT_ADDR" = "null" ]; then
  echo "CONTRACT_ADDR is empty"
  exit 1
fi
```

対応する setup script: なし。インスタンス化された contract address を利用者が指定するためのコマンドである。

すでに contract address が分かっている場合は、直接設定してもよい。

```bash
cd ~/temp/sus_BC2
CONTRACT_ADDR="inj18tpvukcc97896qtxdqrnwf2tpqg6s6yj66yvwx"
source scripts/CW20/load-env.sh
```

対応する shell script: `source scripts/CW20/load-env.sh`

code ID から contract address を探す場合は、次のコマンドも利用できる。

```bash
cd ~/temp/sus_BC2
injectived q wasm list-contract-by-code "$CODE_ID" \
  --node "$NODE" \
  --output json | jq
```

対応する setup script: なし。code ID ごとに個別確認するコマンドである。

### CW20 の token info を確認する

コントラクトが作成できたら、まず contract 情報を確認する。

```bash
cd ~/temp/sus_BC2
injectived q wasm contract "$CONTRACT_ADDR" \
  --node "$NODE" \
  --output json | jq
```

対応する setup script: なし。contract address ごとに個別確認するコマンドである。

次に、`token_info` を query する。

```bash
cd ~/temp/sus_BC2
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' \
  --node "$NODE" \
  --output json | jq
```

対応する setup script: なし。contract address ごとに個別確認するコマンドである。

### CW20 の残高を確認する

送信先アドレスと送金量を設定し、送信元アドレスを確認する。

```bash
cd ~/temp/sus_BC2
RECIPIENT_ADDR="inj1送金先アドレス"
CW20_SEND_AMOUNT="1000000"
source scripts/CW20/load-env.sh

echo "SENDER_ADDR=[$SENDER_ADDR]"
echo "RECIPIENT_ADDR=[$RECIPIENT_ADDR]"
echo "CW20_SEND_AMOUNT=[$CW20_SEND_AMOUNT]"
```

対応する setup script: なし。送信元、送信先、送金量を個別確認するコマンドである。

送信前の CW20 残高を確認する。

```bash
cd ~/temp/sus_BC2
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' \
  --node "$NODE" \
  --output json | jq

injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$RECIPIENT_ADDR"'"}}' \
  --node "$NODE" \
  --output json | jq
```

対応する setup script: なし。contract address と address ごとに個別確認するコマンドである。

### CW20 を送金する

CW20 transfer を実行する。
`1000000` は decimals が `6` の場合、`1 MTK` に相当する。

```bash
cd ~/temp/sus_BC2
CW20_TRANSFER_TXHASH=$(injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend test \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json \
  -y | tee cw20_transfer_tx.json | jq -r '.txhash')

echo "CW20_TRANSFER_TXHASH=$CW20_TRANSFER_TXHASH"
```

対応する setup script: なし。送金先アドレスと contract address ごとに個別実行するコマンドである。

Tx 結果を確認する。

```bash
cd ~/temp/sus_BC2
sleep 6

injectived q tx "$CW20_TRANSFER_TXHASH" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --output json | tee cw20_transfer_result.json | jq '{height:.height, code:.code, raw_log:.raw_log, txhash:.txhash}'
```

対応する setup script: なし。CW20 transfer の TxHash ごとに個別確認するコマンドである。

送信後の CW20 残高を確認する。

```bash
cd ~/temp/sus_BC2
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' \
  --node "$NODE" \
  --output json | jq

injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$RECIPIENT_ADDR"'"}}' \
  --node "$NODE" \
  --output json | jq
```

対応する setup script: なし。transfer 後の address ごとに個別確認するコマンドである。

### CW20 を mint する

インスタンス化時に `mint.minter` として設定したアドレスから、追加発行を行う。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh

injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$MY_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend test \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  -y
```

対応する setup script: なし。mint 権限を持つ address と contract address ごとに個別実行するコマンドである。

### CW20 実行時の注意

- `store` は WASM コードをチェーンへ保存する操作である。
- `instantiate` は保存済み code ID から個別の contract address を作成する操作である。
- `execute` は作成済み contract address に対して `transfer` や `mint` などのメッセージを実行する操作である。
- `query` はチェーン状態を読む操作であり、gas fee を消費しない。
- `cw20-base` の amount は最小単位で指定する。
- decimals が `6` の場合、`1000000` が `1 MTK` に相当する。
- `mint` は、インスタンス化時に設定した minter だけが実行できる。
- `CONTRACT_ADDR` は `CODE_ID` とは別の値である。

