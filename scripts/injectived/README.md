# injectived README

## Kali Linux 上での injectived 実行環境の整備

本実験を Kali Linux 上で実施するためには、Injective の CLI 兼ノードデーモンである `injectived` を利用可能な状態にする必要がある。
本環境では、Linux x86_64 向けの事前ビルド済みバイナリを用いて導入する。

### injectived の導入

`injectived` の取得と展開を行う。

```bash
cd ~/temp
wget https://github.com/InjectiveFoundation/injective-core/releases/latest/download/linux-amd64.zip
unzip linux-amd64.zip
chmod +x injectived
sudo mv injectived /usr/local/bin/
```

対応する shell script: `./scripts/injectived/install-injectived.sh`
対応する setup script: `./setup/normal/04-install-injectived.sh`

`injectived` の実行時に共有ライブラリが見つからない場合は、同梱されている `libwasmvm.x86_64.so` をシステムのライブラリパスへ配置する。

```bash
cd ~/temp
sudo mv libwasmvm.x86_64.so /usr/lib/
sudo ldconfig
injectived version
```

対応する shell script: `./scripts/injectived/install-injectived.sh`
対応する setup script: `./setup/normal/04-install-injectived.sh`

動作確認結果の例を以下に示す。

```text
Version v1.18.3 (b18483b)
Compiled at 20260331-2102 using Go go1.23.9 (amd64)
```

## wallet の作成

本実験では、`test` keyring backend を利用し、パスワード入力を省略して実行する。
まず、鍵名 `testwallet` のウォレットを作成する。

```bash
cd ~/temp/sus_BC2
injectived keys add testwallet --keyring-backend test
```

対応する shell script: `./scripts/injectived/create-test-wallet.sh`
対応する setup script: `./setup/normal/05-create-test-wallet.sh`


次に、Injective testnet 用の共通設定を環境変数として与える。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

対応する shell script: `source scripts/injectived/load-env.sh`

Injective testnet の Faucet は次を利用する。

- https://cloud.google.com/application/web3/faucet/injective/testnet

Faucet 実行後に入金が反映されたかを確認するため、ウォレット残高を確認する。

```bash
cd ~/temp/sus_BC2
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

対応する shell script: `./scripts/injectived/create-test-wallet.sh`
対応する setup script: `./setup/normal/05-create-test-wallet.sh`

出力結果に `inj` の残高が含まれていれば、Faucet による入金が反映されていると判断できる。

## bank send を用いた送金

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

対応する shell script: `source scripts/injectived/load-env.sh`

送金先アドレスも設定する。

```bash
cd ~/temp/sus_BC2
RECIPIENT_ADDR="inj1送金先アドレスをここに入れる"
AMOUNT="1000000000000000inj"
source scripts/injectived/load-env.sh
```

対応する shell script: `source scripts/injectived/load-env.sh`

自分のアドレスも変数に入れる場合は、次のようにする。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
echo "$ADDR"
```

対応する shell script: `source scripts/injectived/load-env.sh`

確認用のコマンドは次のとおりである。

```bash
cd ~/temp/sus_BC2
echo "KEY_NAME=[$KEY_NAME]"
echo "ADDR=[$ADDR]"
echo "RECIPIENT_ADDR=[$RECIPIENT_ADDR]"
echo "CHAIN_ID=[$CHAIN_ID]"
echo "NODE=[$NODE]"
echo "GAS_PRICES=[$GAS_PRICES]"
echo "AMOUNT=[$AMOUNT]"
```

対応する shell script: `source scripts/injectived/load-env.sh`

```bash
cd ~/temp/sus_BC2
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$BANK_SEND_GAS" \
  --broadcast-mode sync \
  -y
```

対応する shell script: `AMOUNT=1000000000000000inj RECIPIENT_ADDR=inj1... CONFIRM_SEND=yes ./scripts/injectived/bank-send.sh`
対応する setup script: `AMOUNT=1000000000000000inj RECIPIENT_ADDR=inj1... CONFIRM_SEND=yes ./setup/normal/06-bank-send.sh`

`1000000000000000inj` は `0.001 INJ` に相当する。
トランザクションは、次の Explorer で確認できる。

- https://www.mintscan.io/injective-testnet
- https://testnet.Explorer.injective.network/

## 送金コマンドの実行例

以下は、`testwallet` を使った送金確認の実行例である。

```bash
cd ~/temp/sus_BC2
RECIPIENT_ADDR=inj13nrc4g4menc78aedxwax86d60wutaam55tv6ug
source scripts/injectived/load-env.sh
```

対応する shell script: `source scripts/injectived/load-env.sh`

鍵情報を確認する。

```bash
cd ~/temp/sus_BC2
echo "KEY_NAME=$KEY_NAME"
injectived keys show "$KEY_NAME" --keyring-backend test
```

対応する shell script: `./scripts/injectived/create-test-wallet.sh`
対応する setup script: `./setup/normal/05-create-test-wallet.sh`

出力例は次のとおりである。

```yaml
KEY_NAME=testwallet
- address: inj1wn80n5shacgsff708sffgyynhkpwdr9jcr3zg8
  name: testwallet
  pubkey: '{"@type":"/injective.crypto.v1beta1.ethsecp256k1.PubKey","key":"A6MIbFNhEMHawyqEI4D701UhkmTHGkuzb1tfR46UsBXu"}'
  type: local
```

残高を確認する。

```bash
cd ~/temp/sus_BC2
injectived query bank balances "inj1wn80n5shacgsff708sffgyynhkpwdr9jcr3zg8" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE"
```

対応する shell script: `./scripts/injectived/create-test-wallet.sh`
対応する setup script: `./setup/normal/05-create-test-wallet.sh`

出力例は次のとおりである。

```yaml
balances:
- amount: "10000000000000000000"
  denom: inj
pagination:
  total: "1"
```

送金する。

```bash
cd ~/temp/sus_BC2
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$BANK_SEND_GAS" \
  --broadcast-mode sync \
  -y
```

対応する shell script: `RECIPIENT_ADDR=inj1... CONFIRM_SEND=yes ./scripts/injectived/bank-send.sh`
対応する setup script: `RECIPIENT_ADDR=inj1... CONFIRM_SEND=yes ./setup/normal/06-bank-send.sh`

出力例は次のとおりである。

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
txhash: 322F692FB340865A0461DC81968C06A7AAECAF1B65375BE1F2D01CCBB88987E6
```
