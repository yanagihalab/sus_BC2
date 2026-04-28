# 実験全体の環境構築

本実験では，WSL 上の Kali Linux 環境を用いて作業を行う。  
まず，Windows の管理者権限付きコマンドプロンプトで WSL を利用し，Kali Linux を導入する。

## WSL を利用した Kali Linux の導入

```bash
wsl --install -d kali-linux
````

導入後は，Kali Linux 上で必要なパッケージを更新し，Python 仮想環境および Java 実行環境などを整備する。

## Python 環境の整備

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv
```

## 作業ディレクトリと Python 仮想環境の作成

```bash
mkdir ~/temp
cd ~/temp
git clone https://github.com/yanagihalab/sus_BC2
cd sus_BC2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

# Kali Linux 上での `injectived` 実行環境の整備

本実験を Kali Linux 上で実施するためには，Injective の CLI 兼ノードデーモンである `injectived` を利用可能な状態にする必要がある。
本環境では，Linux x86_64 向けの事前ビルド済みバイナリを用いて導入する。

## injectived の導入

`injectived` の取得と展開を行う。

```bash
wget https://github.com/InjectiveFoundation/injective-core/releases/latest/download/linux-amd64.zip
unzip linux-amd64.zip
chmod +x injectived
sudo mv injectived /usr/local/bin/
```

`injectived` の実行時に共有ライブラリが見つからない場合は，同梱されている `libwasmvm.x86_64.so` をシステムのライブラリパスへ配置する。

```bash
sudo mv libwasmvm.x86_64.so /usr/lib/
sudo ldconfig
injectived version
```

動作確認結果の例を以下に示す。

```text
Version v1.18.3 (b18483b)
Compiled at 20260331-2102 using Go go1.23.9 (amd64)
```

---

# wallet の作成

まず，鍵名 `mykey` のウォレットを作成する。

```bash
injectived keys add mykey
```

すでにウォレットを作成済みの場合は，鍵を確認し，使用するアドレスを取得する。

```bash
injectived keys list
injectived keys show mykey -a
```

次に，Injective testnet（テストネット）用の共通設定を環境変数として与える。

```bash
export CHAIN_ID=injective-888
export NODE=https://injective-testnet-rpc.publicnode.com:443
export GAS_PRICES=500000000inj
export GAS=1000000
export KEY_NAME=mykey
export MY_ADDR=$(injectived keys show $KEY_NAME -a)
export SUBDENOM=mytoken
```

faucet（フォーセット）実行後に，残高が反映されたかを確認するため，ウォレット残高を確認する。

```bash
injectived query bank balances $MY_ADDR --node=$NODE
```

出力結果に `inj` の残高が含まれていれば，faucet による入金が反映されていると判断できる。

## CW20 コントラクト用の Docker / CosmWasm 環境構築

CW20 コントラクトをビルドするためには，CosmWasm コントラクトを WASM 形式へ変換するビルド環境が必要である。  
本実験では，ホスト環境に Rust / Cargo の詳細なビルド環境を直接構築するのではなく，`cosmwasm/workspace-optimizer` Docker イメージを用いて最適化済み WASM を生成する。

また，本実験では，CosmWasm の `cw-plus` に含まれる `cw20-base` をサンプルコードとして利用する。  
`cw20-base` は，CW20 トークンの基本実装であり，トークン名，シンボル，初期残高，mint 権限などを設定して利用できる。

---

## Docker Engine の導入

`cosmwasm/workspace-optimizer` を利用するためには，Docker Engine が必要である。  
Docker Engine の導入コマンドを以下に示す。

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo docker --version
```

一般ユーザで Docker を実行する場合は，必要に応じて現在のユーザを `docker` グループに追加する。  
Docker グループへの追加コマンドを以下に示す。

```bash
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
```

---

## CW20 サンプルコードの取得

本実験では，CW20 コントラクトを一から実装するのではなく，CosmWasm が提供する `cw-plus` リポジトリ内の `cw20-base` をサンプルコードとして利用する。

`cw-plus` の取得コマンドを以下に示す。

```bash
cd ~/temp
git clone https://github.com/CosmWasm/cw-plus.git
cd cw-plus
ls
```

`cw20-base` コントラクトは，`cw-plus/contracts/cw20-base` に含まれている。  
確認コマンドを以下に示す。

```bash
ls contracts/cw20-base
```

---

## workspace-optimizer によるビルド

取得した `cw20-base` コントラクトを WASM 形式へビルドする。  
本実験では，`cosmwasm/workspace-optimizer` を用いて Docker 上で最適化ビルドを行う。

`cosmwasm/workspace-optimizer` は，CosmWasm コントラクトを再現性のある環境でビルドし，WASM サイズの最適化を行うための Docker イメージである。  
特に，`cw-plus` のように複数のコントラクトを含む workspace 形式のリポジトリをビルドする場合に適している。

`workspace-optimizer` を用いる場合は，`contracts/cw20-base` ディレクトリではなく，`cw-plus` のルートディレクトリで実行する点に注意する。  
ビルドコマンドを以下に示す。

```bash
cd ~/temp/cw-plus

docker run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0
```

ビルドが成功すると，`artifacts` ディレクトリに最適化済みの WASM ファイルが出力される。  
`cw20-base` の場合は，通常，`artifacts/cw20_base.wasm` が生成される。

生成物の確認コマンドを以下に示す。

```bash
ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
```

---

## コントラクトコードの保存

次に，ビルド済みの WASM ファイルを Injective チェーンへ保存する。  
`workspace-optimizer` によって生成された `artifacts/cw20_base.wasm` を指定する。

保存コマンド例を以下に示す。

```bash
injectived tx wasm store artifacts/cw20_base.wasm \
  --from=$KEY_NAME \
  --chain-id=$CHAIN_ID \
  --node=$NODE \
  --gas-prices=$GAS_PRICES \
  --gas=3000000
```

保存に成功すると，トランザクション結果から code ID を確認できる。  
以降のインスタンス化では，この code ID を指定する。

# SimBlock の動作環境構築

SimBlock を利用するためには，Java 実行環境が必要である。
本実験では，SimBlock に付属する Gradle Wrapper を用いてビルドおよび実行を行う。

```bash
sudo apt update
sudo apt install -y openjdk-11-jdk unzip git
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
cd ~/simblock
chmod +x gradlew
./gradlew clean
./gradlew build
./gradlew :simulator:run
```
