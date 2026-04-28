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
pip install -r requests.txt
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

以下が README に貼り付けられる **Markdown 形式**です。TeX の `commandblock` はコードブロックに、節構造は Markdown 見出しに変換しています。

````markdown
## CW20 コントラクト用の Rust / CosmWasm 環境構築

CW20 コントラクトをビルドするためには，Rust および WebAssembly 向けのビルド環境が必要である。  
本実験では，CosmWasm の `cw-plus` に含まれる `cw20-base` をサンプルコードとして利用する。

まず，ビルドに必要な基本パッケージを導入する。

```bash
sudo apt update
sudo apt install -y build-essential curl git pkg-config libssl-dev clang cmake
````

次に，Rust を導入する。

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustc --version
cargo --version
```

CosmWasm コントラクトは WASM 形式にビルドするため，`wasm32-unknown-unknown` ターゲットを追加する。

```bash
rustup target add wasm32-unknown-unknown
```

以上により，CW20 コントラクトをビルドするための Rust / CosmWasm 基本環境が整う。

---

## サンプルコードのビルド

取得した `cw20-base` コントラクトを WASM 形式へビルドする。
ビルド方法には，主に次の 2 通りがある。

* `cosmwasm/workspace-optimizer` を用いて Docker 上で最適化ビルドする方法
* Rust / Cargo を用いてローカル環境で直接ビルドする方法

`cosmwasm/workspace-optimizer` は，CosmWasm コントラクトを再現性のある環境でビルドし，WASM サイズの最適化を行うための Docker イメージである。
特に，`cw-plus` のように複数のコントラクトを含む workspace 形式のリポジトリをビルドする場合に適している。

一方，Rust / Cargo による直接ビルドは，Docker を用いずにローカル環境で動作確認を行う場合に利用できる。

---

## 方法1: `workspace-optimizer` を用いるビルド

本実験で推奨する方法は，`cosmwasm/workspace-optimizer` を用いたビルドである。
この方法では，ホスト側に Rust の詳細なビルド環境を直接構築しなくても，Docker コンテナ内の固定された環境で最適化済み WASM を生成できる。

まず，`cw-plus` リポジトリのルートディレクトリへ移動する。
`contracts/cw20-base` ディレクトリではなく，`cw-plus` のルートディレクトリで実行する点に注意する。

```bash
cd cw-plus
```

次に，`workspace-optimizer` を用いてビルドする。

```bash
docker run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.15.1
```

ビルドが成功すると，`artifacts` ディレクトリに最適化済みの WASM ファイルが出力される。
`cw20-base` の場合は，通常，`artifacts/cw20_base.wasm` が生成される。

生成物を確認する。

```bash
ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
```

なお，環境によっては `cosmwasm/optimizer` を用いる方法も選択できる。
ただし，本資料では教材内のコマンドを統一するため，`cosmwasm/workspace-optimizer` を用いる例を示す。

---

## 方法2: Rust / Cargo を用いる直接ビルド

Docker を用いない場合は，Rust と WASM ビルドターゲットをローカル環境に導入し，Cargo により直接ビルドする。

まず，Rust / Cargo および WASM ターゲットが利用できることを確認する。

```bash
rustc --version
cargo --version
rustup target list --installed | grep wasm32-unknown-unknown
```

`wasm32-unknown-unknown` ターゲットが未導入の場合は，以下のコマンドで追加する。

```bash
rustup target add wasm32-unknown-unknown
```

`cw20-base` ディレクトリへ移動し，WASM をビルドする。

```bash
cd cw-plus/contracts/cw20-base
cargo wasm
cp ../../target/wasm32-unknown-unknown/release/cw20_base.wasm .
```

環境によって `cargo wasm` が利用できない場合は，通常の `cargo build` に WASM ターゲットを指定してビルドする。

```bash
cd cw-plus/contracts/cw20-base
cargo build --release --target wasm32-unknown-unknown
cp ../../target/wasm32-unknown-unknown/release/cw20_base.wasm .
```

この方法で生成した `cw20_base.wasm` も，後続の `injectived tx wasm store` に利用できる。
ただし，チェーンへのデプロイを前提とする場合は，サイズ最適化と再現性の観点から，`workspace-optimizer` を用いたビルドを優先するのが望ましい。

---

## コントラクトコードの保存

次に，ビルド済みの WASM ファイルを Injective チェーンへ保存する。

`workspace-optimizer` を用いた場合は，`artifacts/cw20_base.wasm` を指定する。

```bash
injectived tx wasm store artifacts/cw20_base.wasm \
  --from=$KEY_NAME \
  --chain-id=$CHAIN_ID \
  --node=$NODE \
  --gas-prices=$GAS_PRICES \
  --gas=3000000
```

一方，Rust / Cargo による直接ビルドで `contracts/cw20-base` ディレクトリ内に `cw20_base.wasm` をコピーした場合は，次のように指定する。

```bash
injectived tx wasm store cw20_base.wasm \
  --from=$KEY_NAME \
  --chain-id=$CHAIN_ID \
  --node=$NODE \
  --gas-prices=$GAS_PRICES \
  --gas=3000000
```

保存に成功すると，トランザクション結果から code ID を確認できる。
以降のインスタンス化では，この code ID を指定する。


---

# Docker 環境での実行（該当者のみ）

本実験では，原則として Kali Linux 上に直接導入した `injectived` を用いる。
ただし，Docker 環境で動作確認を行う場合は，次のコマンドを用いる。

```bash
docker run -it --rm injectivelabs/injective-core:v1.14.1 injectived version
```

Docker を利用する場合の導入例を以下に示す。

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo docker --version
```

---

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
