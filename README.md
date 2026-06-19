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

## injectived / wallet / bank send の実行

`injectived` の導入、wallet 作成、Faucet、残高確認、bank send は、次の README に分離している。

- [injectived README](scripts/injectived/README.md)

injectived 用の環境変数は、次の shell script で現在の shell に読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

対応する shell script: `source scripts/injectived/load-env.sh`

## TokenFactory / MTK の実行

TokenFactory を用いた MTK の作成、metadata 設定、mint、送金、確認事項は、次の README に分離している。

- [TokenFactory MTK README](scripts/tokenfactory/README.md)

TokenFactory 用の環境変数は、次の shell script で現在の shell に読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

対応する shell script: `source scripts/tokenfactory/load-env.sh`

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

## CW20 コントラクト用の Docker / CosmWasm 実行

CW20 コントラクトの Docker / CosmWasm 環境構築、WASM build、store、instantiate、query、transfer、mint は、次の README に分離している。

- [CW20 README](scripts/CW20/README.md)

CW20 用の環境変数は、次の shell script で現在の shell に読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
```

対応する shell script: `source scripts/CW20/load-env.sh`

instantiate message は、次の shell script で作成する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
scripts/CW20/create-instantiate-msg.sh
```

対応する shell script: `scripts/CW20/create-instantiate-msg.sh`

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

<!-- ## MacBook ユーザー向けの補足

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

MacBook 上で Docker による簡易検証を行う場合は、[MacBook ユーザー向け: Docker による動作確認](docs/macbook-docker-verification.md) を参照する。 -->
