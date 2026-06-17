# sus_BC2

このリポジトリは、BC2 実験用のブロックチェーン・暗号資産セキュリティ教材である。
Python のプログラムを動かしながら、ブロック、validator、fee market、staking、PoW などの仕組みを確認できる。
日別の Python 実験コード、Injective / SimBlock の環境構築メモ、ブロック提案者を可視化する React アプリを収録している。

プログラミングに慣れていない人は、まずこの README を上から順番に読むとよい。
clone 直後の README に含まれていた環境構築、Injective、wallet、MTK、CW20、SimBlock、送金例の情報は削らず、読みやすい順番に整理している。

## まず知っておくこと

- `リポジトリ` は、実験に使うファイル一式をまとめたフォルダのことである。
- `Python` は、この教材の多くの実験で使うプログラミング言語である。
- `ターミナル` は、コマンドを入力してプログラムを実行する画面である。
- `WSL` は、Windows の中で Linux 環境を使うための仕組みである。
- `Kali Linux` は、本実験で利用する Linux 環境である。
- `README.md` は、リポジトリの説明書である。

## 利用者の実行手順

このリポジトリの利用者は、次の順番で作業する。

1. このリポジトリを clone する。
2. Windows で作業する場合は、Kali Linux をインストールする。
3. Kali Linux 上で実験用の環境構築を行う。

### 1. リポジトリを clone する

まず、このリポジトリを手元の PC に取得する。

```bash
git clone https://github.com/yanagihalab/sus_BC2
cd sus_BC2
```

対応する setup script: `./setup/normal/01-create-workdir-and-python-env.sh`

clone 後は、この README を上から順番に確認する。
Windows ユーザーは、次の Kali Linux インストール手順へ進む。
MacBook ユーザーは、Kali Linux を直接 WSL として使えないため、MacBook 用 Docker 検証手順を参照する。

### 2. Kali Linux をインストールする

Windows で作業する場合は、WSL 上に Kali Linux を用意する。
すでに `wsl -d kali-linux` で Kali Linux を起動できる場合、この手順は省略できる。
具体的な手順は「Windows で作業する場合: WSL / Kali Linux の準備」を参照する。

### 3. Kali Linux 上で環境構築を行う

Kali Linux を起動したあと、リポジトリのフォルダへ移動し、通常実験用の setup script を実行する。

```bash
./setup/normal/wsl-kali-experiment-env.sh
```

対応する setup script: `./setup/normal/wsl-kali-experiment-env.sh`

以降の Python 実験、Injective、SimBlock、可視化アプリの手順は、この README の各節に従って実行する。

## フォルダの見方

```text
Day1/
  1-*.py
  Proposer-visualizer/
Day2/
  2-*.py
Day3/
  3-*.py
  calc_simblock_metrics.sh
docs/
  injective-setup.md
setup/
  normal/
    *.sh
  macbook/
    *.sh
requirements.txt
```

- `Day1/`: ブロック取得、validator 解析、可視化用データ作成の実験である。
- `Day2/`: 待ち行列、fee market、validator selection、staking reward などの実験である。
- `Day3/`: PoW、改ざん検知、nonce 計算、SimBlock 関連の実験である。
- `Day1/Proposer-visualizer/`: Day1 で作った proposer sequence CSV をブラウザで見るための Vite + React アプリである。
- `docs/injective-setup.md`: WSL / Kali Linux 上での Injective、SimBlock、関連ツールの環境構築メモである。
- `./setup/normal/`: WSL / Kali Linux の通常実験で使う shell script である。
- `./setup/macbook/`: MacBook 上の Docker Desktop で確認するための shell script である。
- `requirements.txt`: Python の実験で必要なライブラリ一覧である。

## setup スクリプト一覧

README の主要なコマンドは、`./setup/normal/` または `./setup/macbook/` 配下の shell script としても実行できる。
MacBook の Docker 環境構築と、WSL / Kali Linux の通常実験環境構築は、フォルダと入口スクリプトを分けている。
送金、mint、WASM store などチェーンへ書き込む操作は、誤実行を防ぐために `CONFIRM_SEND=yes` または `CONFIRM_TX=yes` を付けた場合だけ実行される。

### 入口スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/macbook/macbook-docker-env.sh` | MacBook 上の Docker Desktop で Kali Linux ベースの実験環境 image を作成し、基本検証を行う |
| `./setup/normal/wsl-kali-experiment-env.sh` | WSL / Kali Linux 上で通常実験用の基本パッケージ、Python 仮想環境、可視化アプリ依存を整備する |

MacBook では次を実行する。

```bash
./setup/macbook/macbook-docker-env.sh
```

対応する setup script: `./setup/macbook/macbook-docker-env.sh`

WSL / Kali Linux では次を実行する。

```bash
./setup/normal/wsl-kali-experiment-env.sh
```

対応する setup script: `./setup/normal/wsl-kali-experiment-env.sh`

### 部品スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/normal/00-install-kali-packages.sh` | Kali Linux の更新と Python、Java、npm、jq などの基本パッケージ導入 |
| `./setup/normal/01-create-workdir-and-python-env.sh` | `~/temp` 作成、リポジトリ clone、Python 仮想環境作成、`requirements.txt` の install |
| `./setup/normal/02-setup-vscode-ssh.sh` | VS Code Remote - SSH 用の `openssh-server` 設定 |
| `./setup/normal/03-install-simblock.sh` | SimBlock の clone、Java 設定、Gradle build |
| `./setup/normal/04-install-injectived.sh` | `injectived` の取得、展開、`/usr/local/bin` への配置 |
| `./setup/normal/05-create-test-wallet.sh` | `testwallet` の作成と Injective testnet 用環境変数の表示 |
| `./setup/normal/06-bank-send.sh` | `bank send` による送金。実行には `RECIPIENT_ADDR` と `CONFIRM_SEND=yes` が必要 |
| `./setup/normal/07-tokenfactory-mtk.sh` | MTK の denom 作成、metadata 設定、mint、残高確認、送金 |
| `./setup/normal/08-setup-proposer-visualizer.sh` | Proposer Visualizer の `npm install` と起動案内 |
| `./setup/normal/09-install-docker.sh` | Docker Engine の導入 |
| `./setup/normal/10-build-cw20-sample.sh` | `cw-plus` の取得と `workspace-optimizer` による CW20 WASM build |
| `./setup/normal/11-store-cw20-code.sh` | CW20 WASM の Injective への store。実行には `CONFIRM_TX=yes` が必要 |
| `./setup/macbook/verify-in-docker.sh` | README、`./setup/normal/`、`./setup/macbook/` の最小 Docker 検証 |

例:

```bash
./setup/normal/wsl-kali-experiment-env.sh
./setup/normal/04-install-injectived.sh
./setup/normal/05-create-test-wallet.sh
RECIPIENT_ADDR=inj1送金先アドレス CONFIRM_SEND=yes ./setup/normal/06-bank-send.sh
```

対応する setup script: `./setup/normal/wsl-kali-experiment-env.sh`, `./setup/normal/04-install-injectived.sh`, `./setup/normal/05-create-test-wallet.sh`, `./setup/normal/06-bank-send.sh`

## Windows で作業する場合: WSL / Kali Linux の準備

本実験では、WSL 上の Kali Linux 環境を用いて作業を行う。
すでに Kali Linux を起動できる場合は、WSL 2 の確認から始める。
まだ Kali Linux を起動できない場合は、「Kali Linux が未導入の場合」から始める。

### 1. WSL 2 になっているか確認する

PowerShell で次のコマンドを実行する。

```powershell
wsl --list --verbose
```

対応する setup script: なし。Windows PowerShell で実行する WSL 確認コマンドである。

`kali-linux` の `VERSION` が `2` になっていれば WSL 2 で動いている。
`1` になっている場合は、次のコマンドで WSL 2 に変更する。

```powershell
wsl --set-version kali-linux 2
```

対応する setup script: なし。Windows PowerShell で実行する WSL 設定コマンドである。

### 2. Kali Linux を起動する

PowerShell または Windows Terminal で次のコマンドを実行する。

```powershell
wsl -d kali-linux
```

対応する setup script: なし。Windows PowerShell で Kali Linux を起動するコマンドである。

Kali Linux が起動したら、以降の `bash` コマンドは Kali Linux のターミナルで実行する。

### 3. Kali Linux を更新する

Kali Linux を開いて、次のコマンドを実行する。

```bash
sudo apt update
sudo apt upgrade -y
```

対応する setup script: `./setup/normal/00-install-kali-packages.sh`

### 4. 実験に使う基本ツールを入れる

Kali Linux 内で、Python、Git、Java、unzip、npm、jq などを入れる。

```bash
sudo apt install -y python3-pip python3-venv openjdk-11-jdk unzip npm jq git curl nodejs
```

対応する setup script: `./setup/normal/00-install-kali-packages.sh`

インストールできたか確認する。

```bash
python3 --version
git --version
java -version
node --version
npm --version
jq --version
```

対応する setup script: `./setup/normal/00-install-kali-packages.sh`

## Kali Linux が未導入の場合

この節は、WSL / Kali Linux がまだ入っていない場合に読む手順である。
すでに `wsl -d kali-linux` で Kali Linux を起動できる場合は、次の「VS Code から Kali Linux を開く」へ進めばよい。

### 1. Windows のバージョンを確認する

Microsoft の公式手順では、Windows 10 version 2004 以降、または Windows 11 が対象である。
Windows の検索欄で `winver` と入力し、Windows のバージョンを確認する。

### 2. PowerShell を管理者として開く

Windows のスタートメニューで `PowerShell` を検索し、右クリックして「管理者として実行」を選ぶ。
古い手順では管理者権限付きコマンドプロンプトを使う場合もあるが、現在は PowerShell でよい。

### 3. WSL と Kali Linux をインストールする

管理者 PowerShell で次のコマンドを実行する。

```powershell
wsl --install --distribution kali-linux
```

対応する setup script: なし。Windows PowerShell で実行する WSL / Kali Linux インストールコマンドである。

インストール後に再起動を求められた場合は、Windows を再起動する。

上のコマンドでうまくいかない場合は、インストール可能な Linux 一覧を確認する。

```powershell
wsl --list --online
```

対応する setup script: なし。Windows PowerShell で実行する WSL 確認コマンドである。

一覧に `kali-linux` があることを確認してから、もう一度インストールする。

```powershell
wsl --install -d kali-linux
```

対応する setup script: なし。Windows PowerShell で実行する WSL / Kali Linux インストールコマンドである。

### 4. Kali Linux の初期設定をする

インストール後、Kali Linux が起動すると、Linux 用のユーザー名とパスワードを作成する。
ここで入力するパスワードは、画面に文字が表示されない。
何も入力されていないように見えても、実際には入力されている。

### 5. 公式ドキュメント

手順が変わっている場合やエラーが出る場合は、公式ドキュメントも確認すること。

- [Microsoft: WSL のインストール手順](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Kali Linux: Kali WSL の手順](https://www.kali.org/docs/wsl/wsl-preparations/)

## VS Code から Kali Linux を開く

VS Code から Kali Linux 内のファイルを編集する方法は、大きく分けて 2 つある。
通常は `Remote - WSL` を使う方法が簡単である。
SSH 接続として追加したい場合は、`Remote - SSH` を使う。

### 方法 A: Remote - WSL で開く

VS Code に `WSL` 拡張機能を入れる。
その後、VS Code で `F1` または `Ctrl + Shift + P` を押し、次のコマンドを選ぶ。

```text
WSL: Connect to WSL using Distro
```

表示された一覧から `kali-linux` を選ぶ。
接続後、VS Code の左下に `WSL: kali-linux` のように表示されれば、Kali Linux 側で作業できている。

Kali Linux のターミナルから直接 VS Code を開く場合は、リポジトリのフォルダで次のコマンドを実行する。

```bash
code .
```

対応する setup script: なし。VS Code を開くための手動コマンドである。

### 方法 B: Remote - SSH に kali-linux を追加する

VS Code の `Remote - SSH` に Kali Linux を追加する場合は、Kali Linux 側で SSH サーバーを起動し、Windows 側の VS Code から接続する。

Kali Linux を開き、SSH サーバーを入れる。

```bash
sudo apt update
sudo apt install -y openssh-server
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

WSL 内の SSH サーバーは、Windows 側の SSH と衝突しないように `2222` 番ポートで起動すると扱いやすい。
`/etc/ssh/sshd_config` を開く。

```bash
sudo nano /etc/ssh/sshd_config
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

次の設定を探し、なければファイルの最後に追加する。

```text
Port 2222
PasswordAuthentication yes
PermitRootLogin no
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

設定後、SSH サーバーを再起動する。

```bash
sudo service ssh restart
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

設定ファイルの構文と SSH サーバーの状態を確認する。

```bash
sudo sshd -t
sudo service ssh status
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

`sudo sshd -t` は、設定に問題がなければ何も表示せず終了する。
`sudo service ssh status` で `sshd is running` のように表示されれば、SSH サーバーは起動している。

Windows の PowerShell から接続できるか確認する。
`<kaliユーザー名>` は、Kali Linux の初期設定で作ったユーザー名に置き換える。

```powershell
ssh <kaliユーザー名>@127.0.0.1 -p 2222
```

対応する setup script: なし。Windows PowerShell から SSH 接続を確認するコマンドである。

接続できたら、VS Code で `F1` または `Ctrl + Shift + P` を押し、次のコマンドを選ぶ。

```text
Remote-SSH: Add New SSH Host...
```

入力欄に次の形式で入力する。

```text
ssh <kaliユーザー名>@127.0.0.1 -p 2222
```

SSH 設定ファイルの選択を求められたら、通常は Windows ユーザーの `~/.ssh/config` を選ぶ。
手動で設定を書く場合は、次のようにする。

```sshconfig
Host kali-linux
  HostName 127.0.0.1
  User <kaliユーザー名>
  Port 2222
```

対応する setup script: なし。Windows 側の SSH 設定ファイルへ手動で書く内容である。

追加後、VS Code で次のコマンドを選ぶ。

```text
Remote-SSH: Connect to Host...
```

一覧から `kali-linux` を選ぶ。
接続後、VS Code の左下に `SSH: kali-linux` のように表示されれば、SSH 経由で Kali Linux に接続できている。

WSL を再起動した後に SSH 接続できない場合は、Kali Linux 側で次のコマンドを実行する。

```bash
sudo service ssh restart
```

対応する setup script: `./setup/normal/02-setup-vscode-ssh.sh`

## 作業ディレクトリと Python 仮想環境の作成

任意の作業ディレクトリとして、ここでは `~/temp` を作成する。

```bash
mkdir ~/temp
cd ~/temp
git clone https://github.com/yanagihalab/sus_BC2
cd sus_BC2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

対応する setup script: `./setup/normal/01-create-workdir-and-python-env.sh`

以降、各 Python スクリプトは、特に指定がない限りリポジトリの一番上のフォルダから実行する。

```bash
python3 Day1/1-1_block-fetch.py
python3 Day2/2-1mm1_queue.py
python3 Day3/3-1_btc_mining.py
```

対応する setup script: なし。実験用 Python ファイルは個別に実行する。

一部の Python ファイルには、`*__*` のような仮の値が残っている。
これは、対象チェーン、入力ファイル、試行回数、validator 数、block 数などを実験条件に合わせて自分で入れる場所である。
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

本実験では、test mode を利用して password を設定せずに実行する。
まず、鍵名 `testwallet` のウォレットを作成する。

```bash
injectived keys add testwallet --keyring-backend test
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

すでにウォレットを作成済みの場合は、鍵を確認し、使用するアドレスを取得する。

```bash
injectived keys list --keyring-backend test
injectived keys show testwallet -a --keyring-backend test
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

次に、Injective testnet 用の共通設定を環境変数として与える。

```bash
export CHAIN_ID=injective-888
export NODE=https://injective-testnet-rpc.publicnode.com:443
export GAS_PRICES=500000000inj
export GAS=1000000
export KEY_NAME=testwallet
export MY_ADDR=$(injectived keys show "$KEY_NAME" -a --keyring-backend test)
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

faucet 実行後に残高が反映されたかを確認するため、ウォレット残高を確認する。

```bash
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

対応する setup script: `./setup/normal/05-create-test-wallet.sh`

出力結果に `inj` の残高が含まれていれば、faucet による入金が反映されていると判断できる。

## bank send を用いた送金

```bash
export KEY_NAME="testwallet"
export CHAIN_ID="injective-888"
export NODE="https://injective-testnet-rpc.publicnode.com:443"
export GAS_PRICES="500000000inj"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

送金先アドレスも設定する。

```bash
export RECIPIENT_ADDR="inj1送金先アドレスをここに入れる"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

自分のアドレスも変数に入れる場合は、次のようにする。

```bash
export ADDR=$(injectived keys show "$KEY_NAME" -a --keyring-backend test)
echo "$ADDR"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

確認用のコマンドは次のとおりである。

```bash
echo "KEY_NAME=[$KEY_NAME]"
echo "ADDR=[$ADDR]"
echo "RECIPIENT_ADDR=[$RECIPIENT_ADDR]"
echo "CHAIN_ID=[$CHAIN_ID]"
echo "NODE=[$NODE]"
echo "GAS_PRICES=[$GAS_PRICES]"
```

対応する setup script: `./setup/normal/06-bank-send.sh`

```bash
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

`1000000000000000inj` は `0.001 INJ` である。
トランザクションは次の explorer で確認できる。

- https://www.mintscan.io/injective-testnet
- https://testnet.explorer.injective.network/

## MTK の実行

### 1. 環境変数を設定する

```bash
export KEY_NAME="testwallet"
export CHAIN_ID="injective-888"
export NODE="https://injective-testnet-rpc.publicnode.com:443"
export GAS_PRICES="500000000inj"
export GAS="300000"
export SUBDENOM="mtk"
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh`

自分のアドレスと TokenFactory denom を設定する。

```bash
export CREATOR_ADDR=$(injectived keys show "$KEY_NAME" -a --keyring-backend test)
export DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"

echo "CREATOR_ADDR=$CREATOR_ADDR"
echo "DENOM=$DENOM"
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh`

`DENOM` は次の形式になる必要がある。

```text
factory/inj.../mtk
```

### 2. denom を作成する

```bash
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
injectived query tx <TXHASH> \
  --node="$NODE" \
  -o json | jq
```

対応する setup script: なし。`<TXHASH>` ごとに個別確認するコマンドである。

### 3. metadata を設定する

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
injectived query bank balances "$CREATOR_ADDR" \
  --node="$NODE" \
  --chain-id="$CHAIN_ID" \
  -o json | jq
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh balance`

### 6. トークンを送金する

送金先アドレスを設定する。

```bash
export RECIPIENT_ADDR="inj1送金先アドレス"
```

対応する setup script: `RECIPIENT_ADDR=inj1... CONFIRM_TX=yes ./setup/normal/07-tokenfactory-mtk.sh send`

`1 MTK` を送金する場合は次のコマンドである。

```bash
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
injectived query bank balances "$RECIPIENT_ADDR" \
  --node="$NODE" \
  --chain-id="$CHAIN_ID" \
  -o json | jq
```

対応する setup script: なし。送金先アドレスごとに個別確認するコマンドである。

`set-denom-metadata` で失敗する場合は、まず次を確認するべきである。

```bash
echo "DENOM=[$DENOM]"
```

対応する setup script: `./setup/normal/07-tokenfactory-mtk.sh env`

ここが空であれば、`invalid metadata base denom: invalid denom:` が発生する。
正しくは次のように表示される必要がある。

```text
DENOM=[factory/inj.../mtk]
```

## Proposer Visualizer の環境構築

`Proposer Visualizer` は、Day1 の実験で作った proposer sequence CSV をブラウザで見るための Vite + React アプリである。
このアプリを使うには、Python とは別に Node.js と npm が必要である。

```bash
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
npm run dev -- --host 0.0.0.0
```

対応する setup script: `RUN_VISUALIZER=yes ./setup/normal/08-setup-proposer-visualizer.sh`

依存関係が壊れている場合は、生成物を削除して依存パッケージを入れ直す。
`node_modules/`、build 出力、生成された manifest は Git 管理対象外である。

```bash
rm -rf node_modules package-lock.json
npm install
```

対応する setup script: `RESET_NODE_MODULES=yes ./setup/normal/08-setup-proposer-visualizer.sh`

## CW20 コントラクト用の Docker / CosmWasm 環境構築

CW20 コントラクトをビルドするためには、CosmWasm コントラクトを WASM 形式へ変換するビルド環境が必要である。
本実験では、ホスト環境に Rust / Cargo の詳細なビルド環境を直接構築するのではなく、`cosmwasm/workspace-optimizer` Docker イメージを用いて最適化済み WASM を生成する。

また、本実験では、CosmWasm の `cw-plus` に含まれる `cw20-base` をサンプルコードとして利用する。
`cw20-base` は、CW20 トークンの基本実装であり、トークン名、シンボル、初期残高、mint 権限などを設定して利用できる。

### Docker Engine の導入

`cosmwasm/workspace-optimizer` を利用するためには、Docker Engine が必要である。
Docker Engine の導入コマンドを以下に示す。

```bash
sudo apt update
sudo apt install -y docker.io
sudo service docker start
sudo docker --version
```

対応する setup script: `./setup/normal/09-install-docker.sh`

一般ユーザで Docker を実行する場合は、必要に応じて現在のユーザを `docker` グループに追加する。
Docker グループへの追加コマンドを以下に示す。

```bash
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
ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
```

対応する setup script: `./setup/normal/10-build-cw20-sample.sh`

### コントラクトコードの保存

次に、ビルド済みの WASM ファイルを Injective チェーンへ保存する。
`workspace-optimizer` によって生成された `artifacts/cw20_base.wasm` を指定する。

保存コマンド例を以下に示す。

```bash
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

## 送金のコマンド訂正

以下は、`testwallet` を使った送金確認の実行例である。

```bash
export KEY_NAME=testwallet
export RECIPIENT_ADDR=inj13nrc4g4menc78aedxwax86d60wutaam55tv6ug
export CHAIN_ID=injective-888
export NODE=https://injective-testnet-rpc.publicnode.com:443
export GAS_PRICES=500000000inj
```

対応する setup script: `./setup/normal/06-bank-send.sh`

鍵情報を確認する。

```bash
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
python3 Day1/1-1_block-fetch.py
```

対応する setup script: なし。実験用 Python ファイルは個別に実行する。

### ライブラリが見つからない

仮想環境を有効にしてから、もう一度ライブラリを入れる。

```bash
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

- `command.md` と `2-4command.md` には、実験時に使用したコマンドや作業メモを残している。
- `jikken_txt.pdf` は元の実験資料である。
- `command.env.example` はローカル環境変数の例である。秘密鍵、mnemonic、個人用 RPC 認証情報などは commit しないこと。
- MacBook 上で Docker による簡易検証を行う場合は、[MacBook ユーザー向け: Docker による動作確認](docs/macbook-docker-verification.md) を参照する。

## Kali Linux を WSL から登録解除する場合

Kali Linux の WSL 環境を削除して作り直す場合は、PowerShell で次のコマンドを実行する。
この操作を行うと、Kali Linux 内のファイル、設定、インストール済み package は削除される。
必要なファイルは事前に退避する必要がある。

```powershell
wsl --unregister kali-linux
```

対応する setup script: なし。Windows PowerShell で実行する WSL 登録解除コマンドである。

登録名が異なる場合は、先に次のコマンドで名前を確認する。

```powershell
wsl --list --verbose
```

対応する setup script: なし。Windows PowerShell で実行する WSL 確認コマンドである。
