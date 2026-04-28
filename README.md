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
python3 -m venv venv
source venv/bin/activate
git clone XXXX
pip install -r requests.txt
```

> `XXXX` には，配布されたリポジトリの URL を指定する。
> `requests.txt` というファイル名を使用している場合はそのまま実行する。一般的な Python プロジェクトでは `requirements.txt` という名前が使われることもあるため，配布ファイル名を確認すること。

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
