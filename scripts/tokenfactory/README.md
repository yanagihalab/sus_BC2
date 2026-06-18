# TokenFactory MTK README

## MTK の実行

### 1. 環境変数を設定する

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

自分のアドレスと TokenFactory denom を設定する。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh

echo "CREATOR_ADDR=$CREATOR_ADDR"
echo "DENOM=$DENOM"
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

`DENOM` は次の形式になる必要がある。

```text
factory/inj.../mtk
```

### 2. denom を作成する

```bash
cd ~/temp/sus_BC2
injectived tx tokenfactory create-denom \
  "$SUBDENOM" \
  "My Token" \
  "MTK" \
  6 \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh create-denom`

TxHash が出たら、次のコマンドで結果を確認する。

```bash
cd ~/temp/sus_BC2
injectived query tx <TXHASH> \
  --node="$NODE" \
  -o json | jq
```

対応する setup script: なし。`<TXHASH>` ごとに個別確認するコマンドである。

### 3. metadata を設定する

```bash
cd ~/temp/sus_BC2
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
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh set-metadata`

### 4. トークンを mint する

ここでは `1000 MTK` 相当を mint する。
`decimals=6` であるため、`1000 MTK = 1000000000` base unit である。

```bash
cd ~/temp/sus_BC2
injectived tx tokenfactory mint \
  "1000000000$DENOM" \
  "$CREATOR_ADDR" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh mint`

### 5. 残高を確認する

```bash
cd ~/temp/sus_BC2
injectived query bank balances "$CREATOR_ADDR" \
  --node="$NODE" \
  --chain-id="$CHAIN_ID" \
  -o json | jq
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh balance`

### 6. トークンを送金する

送金先アドレスを設定する。

```bash
cd ~/temp/sus_BC2
RECIPIENT_ADDR="inj1送金先アドレス"
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

`1 MTK` を送金する場合は次のコマンドである。

```bash
cd ~/temp/sus_BC2
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "1000000$DENOM" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `RECIPIENT_ADDR=inj1... SEND_AMOUNT=1000000 CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh send`

送金先の残高確認は次のとおりである。

```bash
cd ~/temp/sus_BC2
injectived query bank balances "$RECIPIENT_ADDR" \
  --node="$NODE" \
  --chain-id="$CHAIN_ID" \
  -o json | jq
```

対応する setup script: なし。送金先アドレスごとに個別確認するコマンドである。

`set-denom-metadata` で失敗する場合は、まず次を確認するべきである。

```bash
cd ~/temp/sus_BC2
echo "DENOM=[$DENOM]"
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh env`

ここが空であれば、`invalid metadata base denom: invalid denom:` が発生する。
正しくは次のように表示される必要がある。

```text
DENOM=[factory/inj.../mtk]
```

### 7. MTK 作成時のフィードバックと確認事項

以下は、Injective Testnet で TokenFactory を用いて MTK を作成するときに発生しやすいエラーと確認事項である。
例として、次の環境変数を使う。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

#### `denom does not exist`

次のようなエラーが出る場合がある。

```text
failed to execute message; message index: 0: denom: factory/inj.../mtk: denom does not exist
```

原因は、`factory/.../mtk` がまだ TokenFactory で作成されていないことである。
次のコマンドで、作成済み denom を確認する。

```bash
cd ~/temp/sus_BC2
injectived q tokenfactory denoms-from-creator "$CREATOR_ADDR" \
  --node="$NODE" \
  --output json | jq
```

対応する setup script: なし。creator address ごとに個別確認するコマンドである。

`denoms: []` の場合、denom は未作成である。
その場合は `create-denom` を先に実行する必要がある。

#### `create-denom` に必要な残高

`create-denom` には、gas fee とは別に `1 INJ` の denom creation fee が必要である。
残高が足りない場合、次のようなエラーが出る。

```text
spendable balance 498950000000000000inj is smaller than 1000000000000000000inj: insufficient funds
```

必要残高の目安は次のとおりである。

```text
1 INJ + gas fee
```

現在の gas 設定が次の場合を考える。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

gas fee は次の計算になる。

```text
500000000 * 300000 = 150000000000000inj
= 0.00015 INJ
```

したがって、最低必要額は次のとおりである。

```text
1.00015 INJ 以上
```

安全には `1.1 INJ` 以上を用意する。

#### `insufficient fee`

次のようなエラーが出る場合がある。

```text
insufficient fees; got: 48000000000000inj required: 150000000000000inj: insufficient fee
```

原因は、`GAS_PRICES="160000000inj"` では、この RPC / testnet 環境で要求される下限手数料に届かないことである。
`GAS=300000` の場合、次の計算になる。

```text
160000000 * 300000 = 48000000000000inj
```

要求値が `150000000000000inj` の場合、必要な gas price は次のとおりである。

```text
150000000000000 / 300000 = 500000000inj
```

推奨設定は次のとおりである。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

#### `height: "0"` は確定成功ではない

`txhash` が返っても、次のように出る場合がある。

```text
height: "0"
gas_used: "0"
gas_wanted: "0"
```

これはブロードキャストできただけで、ブロックに入った成功結果ではない。
TxHash が出たあと、次のコマンドで結果を確認する。

```bash
cd ~/temp/sus_BC2
TXHASH="ここにTxHashを入れる"

injectived q tx "$TXHASH" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --output json | jq '{height:.height, code:.code, raw_log:.raw_log, txhash:.txhash}'
```

対応する setup script: なし。TxHash ごとに個別確認するコマンドである。

成功条件は次のとおりである。

```json
{
  "code": 0
}
```

#### denom 作成確認

denom 作成後は、次のコマンドで `factory/.../mtk` が存在するか確認する。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh

injectived q tokenfactory denoms-from-creator "$CREATOR_ADDR" \
  --node="$NODE" \
  --output json | jq
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

成功していれば、次のように表示される。

```json
{
  "denoms": [
    "factory/inj.../mtk"
  ]
}
```

#### create-denom 実行例

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh

injectived tx tokenfactory create-denom "$SUBDENOM" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh create-denom`

#### mint 実行例

denom 作成後に実行する。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh

injectived tx tokenfactory mint 1000000"$DENOM" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

対応する setup script: `MINT_AMOUNT=1000000 CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh mint`

#### mint 確認

```bash
cd ~/temp/sus_BC2
injectived q bank balances "$CREATOR_ADDR" \
  --node="$NODE" \
  --output json | jq --arg DENOM "$DENOM" '
    {
      address: "'"$CREATOR_ADDR"'",
      denom: $DENOM,
      balance: (
        .balances[]?
        | select(.denom == $DENOM)
      )
    }
  '
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh balance`

成功していれば、次のように `amount` が表示される。

```json
{
  "address": "inj...",
  "denom": "factory/inj.../mtk",
  "balance": {
    "denom": "factory/inj.../mtk",
    "amount": "1000000"
  }
}
```

`balance: null` の場合、そのアドレスにはまだ MTK が存在しない。

#### `07-tokenfactory-mtk.sh` を使う場合

`07-tokenfactory-mtk.sh` は action 引数が必要である。

環境確認:

```bash
cd ~/temp/sus_BC2
./setup/normal/07-tokenfactory-mtk.sh env
```

denom 作成:

```bash
cd ~/temp/sus_BC2
CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh create-denom
```

mint:

```bash
cd ~/temp/sus_BC2
MINT_AMOUNT=1000000 \
CONFIRM_TX=yes \
./setup/normal/07-tokenfactory-mtk.sh mint
```

残高確認:

```bash
cd ~/temp/sus_BC2
./setup/normal/07-tokenfactory-mtk.sh balance
```

送金:

```bash
cd ~/temp/sus_BC2
RECIPIENT_ADDR="inj1..." \
SEND_AMOUNT=1000000 \
CONFIRM_TX=yes \
./setup/normal/07-tokenfactory-mtk.sh send
```

#### 作業上の注意

- `create-denom` は一度だけ実行する。
- 成功後に同じ `SUBDENOM` で再実行すると、既存 denom エラーになる可能性がある。
- `denoms: []` の場合は denom 未作成である。
- `mint` や `send` は denom 作成後に行う。
- `inj` は 18 桁小数である。
- `1000000000000000000inj` は `1 INJ` である。
- `500000000000000000inj` は `0.5 INJ` である。
- `1000000factory/.../mtk` は MTK の最小単位で `1,000,000` 単位である。
- `create-denom` には gas fee とは別に `1 INJ` が必要である。
- 現在の環境では `GAS_PRICES=500000000inj` が実質的な下限である。

