# sus_BC2
## 実行手順

本リポジトリの利用者は、次の順番で作業する。

1. Windows で作業する場合は、WSL 上に Kali Linux をインストールする。
2. Kali Linux の初期設定を行う。
3. Kali Linux を更新し、実験に必要な基本ツールをインストールする。
4. このリポジトリを clone する。
5. リポジトリルートで実験用の環境構築スクリプトを実行する。

以降のコマンドは、特に指定がない限り、Kali Linux のターミナルで実行する。

### 1. Kali Linux をインストールする

Windows で作業する場合は、WSL 上に Kali Linux を用意する。

```bash
wsl --install -d kali-linux
```

### 2. Kali Linux の初期設定をする

インストール後に Kali Linux が起動したら、Linux 用のユーザー名とパスワードを作成する。
パスワードの入力中は画面に文字が表示されないが、実際には入力されている。

### 3. Kali Linux を更新する

Kali Linux を開き、次のコマンドを実行する。

```bash
sudo apt update
sudo apt upgrade -y
```

### 4. リポジトリを clone する

Kali Linux を起動したあと、本リポジトリを手元の PC に取得する。

```bash
mkdir -p ~/temp
cd ~/temp
git clone https://github.com/yanagihalab/sus_BC2
cd sus_BC2
```

対応する setup script: `./setup/normal/01-create-workdir-and-python-env.sh`


対応する setup script: `./setup/normal/00-install-kali-packages.sh`

### 5. 実験に使う基本ツールを入れる

Kali Linux 内に、Python、Git、Java、unzip、npm、jq などをインストールする。

```bash
sudo apt install -y python3-pip python3-venv openjdk-11-jdk unzip npm jq git curl nodejs
```

対応する setup script: `./setup/normal/00-install-kali-packages.sh`

インストールできたかを確認する。

```bash
python3 --version
git --version
java -version
node --version
npm --version
jq --version
```

対応する setup script: `./setup/normal/00-install-kali-packages.sh`

### 6. Kali Linux 上で環境構築を行う

リポジトリのフォルダへ移動し、通常実験用の setup script を実行する。

```bash
cd ~/temp/sus_BC2
./setup/normal/wsl-kali-experiment-env.sh
```

対応する setup script: `./setup/normal/wsl-kali-experiment-env.sh`

## VS Code から Kali Linux を開く

VS Code から Kali Linux 内のファイルを編集する場合は、通常 `Remote - WSL` を利用する。
SSH 接続として追加したい場合は、`Remote - SSH` を利用する。

### Remote - WSL で開く

VS Code に WSL 拡張機能をインストールし、Kali Linux に接続する。
Kali Linux のターミナルから直接 VS Code を開く場合は、リポジトリのフォルダで次のコマンドを実行する。

```bash
cd ~/temp/sus_BC2
code .
```

## 作業ディレクトリと Python 仮想環境の作成

リポジトリを clone したあと、Python 仮想環境を作成し、必要なライブラリをインストールする。

```bash
cd ~/temp/sus_BC2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

対応する setup script: `./setup/normal/01-create-workdir-and-python-env.sh`

以降、各 Python スクリプトは、特に指定がない限りリポジトリルートから実行する。

```bash
cd ~/temp/sus_BC2
python3 Day1/1-1_block-fetch.py
python3 Day2/2-1mm1_queue.py
python3 Day3/3-1_btc_mining.py
```

対応する setup script: なし。実験用 Python ファイルは個別に実行する。

一部の Python ファイルには、`*__*` のような仮の値が残っている。
これは、対象チェーン、入力ファイル、試行回数、validator 数、block 数などを実験条件に合わせて入力する場所である。
`*__*` が残ったまま実行すると、Python のエラーになることがある。

## SimBlock の動作環境構築

SimBlock は Day3 で使用する。
SimBlock を利用するためには、Java 実行環境が必要である。
本実験では、SimBlock に付属する Gradle Wrapper を用いてビルドおよび実行を行う。

```bash
cd ~/temp
git clone https://github.com/dsg-titech/simblock
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
cd ~/temp/simblock
chmod +x gradlew
./gradlew clean
./gradlew build
./gradlew :simulator:run
```

対応する setup script: `./setup/normal/03-install-simblock.sh`

必要パッケージを含めて実行する場合は、次の流れである。

```bash
sudo apt update
sudo apt install -y openjdk-11-jdk unzip git
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
cd ~/temp/simblock
chmod +x gradlew
./gradlew clean
./gradlew build
./gradlew :simulator:run
```

対応する setup script: `./setup/normal/03-install-simblock.sh`

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

対応する setup script: `./setup/normal/04-install-injectived.sh`

`injectived` の実行時に共有ライブラリが見つからない場合は、同梱されている `libwasmvm.x86_64.so` をシステムのライブラリパスへ配置する。

```bash
cd ~/temp
sudo mv libwasmvm.x86_64.so /usr/lib/
sudo ldconfig
injectived version
```

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

対応する setup script: `./setup/normal/05-create-test-wallet.sh`


次に、Injective testnet 用の共通設定を環境変数として与える。

```bash
cd ~/temp/sus_BC2
export CHAIN_ID=injective-888
export NODE=https://injective-testnet-rpc.publicnode.com:443
export GAS_PRICES=500000000inj
export GAS=1000000
export KEY_NAME=testwallet
export MY_ADDR=$(injectived keys show "$KEY_NAME" -a --keyring-backend test)
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

Faucet 実行後に入金が反映されたかを確認するため、ウォレット残高を確認する。

```bash
cd ~/temp/sus_BC2
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

出力結果に `inj` の残高が含まれていれば、Faucet による入金が反映されていると判断できる。

## bank send を用いた送金

```bash
cd ~/temp/sus_BC2
export KEY_NAME="testwallet"
export CHAIN_ID="injective-888"
export NODE="https://injective-testnet-rpc.publicnode.com:443"
export GAS_PRICES="500000000inj"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

送金先アドレスも設定する。

```bash
cd ~/temp/sus_BC2
export RECIPIENT_ADDR="inj1送金先アドレスをここに入れる"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

自分のアドレスも変数に入れる場合は、次のようにする。

```bash
cd ~/temp/sus_BC2
export ADDR=$(injectived keys show "$KEY_NAME" -a --keyring-backend test)
echo "$ADDR"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

確認用のコマンドは次のとおりである。

```bash
cd ~/temp/sus_BC2
echo "KEY_NAME=[$KEY_NAME]"
echo "ADDR=[$ADDR]"
echo "RECIPIENT_ADDR=[$RECIPIENT_ADDR]"
echo "CHAIN_ID=[$CHAIN_ID]"
echo "NODE=[$NODE]"
echo "GAS_PRICES=[$GAS_PRICES]"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

```bash
cd ~/temp/sus_BC2
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "1000000000000000inj" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas=200000 \
  --broadcast-mode sync \
  -y
```

対応する setup script: `./setup/normal/06-bank-send.sh`

`1000000000000000inj` は `0.001 INJ` に相当する。
トランザクションは、次の Explorer で確認できる。

- https://www.mintscan.io/injective-testnet
- https://testnet.Explorer.injective.network/

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

## Proposer Visualizer の環境構築

`Proposer Visualizer` は、Day1 の実験で作った proposer sequence CSV をブラウザで見るための Vite + React アプリである。
このアプリを使うには、Python とは別に Node.js と npm が必要である。

```bash
cd ~/temp/sus_BC2
sudo apt install -y nodejs npm
cd Day1/Proposer-visualizer
npm install
npm run start
```

対応する setup script: `RUN_VISUALIZER=yes ./setup/normal/08-setup-proposer-visualizer.sh`

`npm run start` は `out/` 配下の CSV を読み取り、起動時に `out/index.json` を生成してから Vite 開発サーバを起動する。
起動後、ターミナルに表示される URL をブラウザで開く。
通常は `http://localhost:5173` で確認できる。

手動で Vite を起動する場合は、次のコマンドでもよい。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
npm run dev -- --host 0.0.0.0
```

対応する setup script: `RUN_VISUALIZER=yes ./setup/normal/08-setup-proposer-visualizer.sh`

依存関係が壊れている場合は、生成物を削除して依存パッケージを入れ直す。
`node_modules/`、build 出力、生成された manifest は Git 管理対象外である。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
rm -rf node_modules package-lock.json
npm install
```

対応する setup script: `RESET_NODE_MODULES=yes ./setup/normal/08-setup-proposer-visualizer.sh`

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

## 送金コマンドの実行例

以下は、`testwallet` を使った送金確認の実行例である。

```bash
cd ~/temp/sus_BC2
export KEY_NAME=testwallet
export RECIPIENT_ADDR=inj13nrc4g4menc78aedxwax86d60wutaam55tv6ug
export CHAIN_ID=injective-888
export NODE=https://injective-testnet-rpc.publicnode.com:443
export GAS_PRICES=500000000inj
```

対応する setup script: `./setup/normal/06-bank-send.sh`

鍵情報を確認する。

```bash
cd ~/temp/sus_BC2
echo "KEY_NAME=$KEY_NAME"
injectived keys show "$KEY_NAME" --keyring-backend test
```

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
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "100000000inj" \
  --from="$KEY_NAME" \
  --keyring-backend test \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas=200000 \
  --broadcast-mode sync \
  -y
```

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

## 困ったとき

### `python` コマンドが見つからない

環境によっては `python` ではなく `python3` を使う。

```bash
cd ~/temp/sus_BC2
python3 Day1/1-1_block-fetch.py
```

対応する setup script: なし。実験用 Python ファイルは個別に実行する。

### ライブラリが見つからない

仮想環境を有効にしてから、もう一度ライブラリを入れる。

```bash
cd ~/temp/sus_BC2
source venv/bin/activate
pip install -r requirements.txt
```

対応する setup script: `./setup/normal/01-create-workdir-and-python-env.sh`

### `*__*` のエラーが出る

実行した Python ファイルの中に、まだ仮の値が残っている可能性がある。
ファイルを開いて `*__*` を探し、実験条件に合わせて値を入れる。

### SSH 接続できない

WSL を再起動した後に SSH 接続できない場合は、Kali Linux 側で SSH サーバーを再起動する。

```bash
sudo service ssh restart
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

## 補足

- `command.md` には、実験時に使用したコマンドや作業メモを残している。
- `jikken_txt.pdf` は元の実験資料である。
- `command.env.example` はローカル環境変数の例である。秘密鍵、mnemonic、個人用 RPC 認証情報などは コミットしないこと。

## Kali Linux を WSL から登録解除する場合

Kali Linux の WSL 環境を削除して作り直す場合は、Windows のコマンドプロンプトで次のコマンドを実行する。
この操作を行うと、Kali Linux 内のファイル、設定、インストール済み パッケージは削除される。
必要なファイルは事前に退避しておく必要がある。

```cmd
wsl --unregister kali-linux
```

対応する setup script: なし。Windows のコマンドプロンプトで実行する WSL 登録解除コマンドである。

登録名が異なる場合は、先に次のコマンドで名前を確認する。

```cmd
wsl --list --verbose
```

対応する setup script: なし。Windows のコマンドプロンプトで実行する WSL 確認コマンドである。

## MacBook ユーザー向けの補足

MacBook 上で作業する場合は、Docker Desktop を利用して Kali Linux ベースの実験環境イメージを作成し、README、`./setup/normal/`、`./setup/macbook/` の最小検証を行う。
MacBook 向けの Docker 環境構築と、WSL / Kali Linux の通常実験環境構築は、フォルダと入口スクリプトを分けている。

### MacBook 用入口スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/macbook/macbook-docker-env.sh` | MacBook 上の Docker Desktop で Kali Linux ベースの実験環境 image を作成し、基本検証を行う |

MacBook では次を実行する。

```bash
cd ~/temp/sus_BC2
./setup/macbook/macbook-docker-env.sh
```

対応する setup script: `./setup/macbook/macbook-docker-env.sh`

### MacBook 用スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/macbook/verify-in-docker.sh` | README、`./setup/normal/`、`./setup/macbook/` の最小 Docker 検証 |

MacBook で通常部品を実行する場合は、`./setup/macbook/00-install-kali-packages.sh` から `./setup/macbook/11-store-cw20-code.sh` までの同名 wrapper を使う。
これらは `./setup/normal/` の本体を呼び出す入口である。

MacBook 上で Docker による簡易検証を行う場合は、[MacBook ユーザー向け: Docker による動作確認](docs/macbook-docker-verification.md) を参照する。
