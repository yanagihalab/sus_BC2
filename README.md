# sus_BC2

## 実行手順

本リポジトリの利用者は、次の順番で作業する。

1. Windows で作業する場合は、WSL を更新し、Kali Linux をインストールする。
2. 本リポジトリをクローンする。
3. リポジトリルートで実験用の環境構築スクリプトを実行する。

以降のコマンドは、特に指定がない限り、Kali Linux のターミナルで実行する。

### 1. WSL を更新し、Kali Linux をインストールする

Windows で作業する場合は、Windows の PowerShell またはコマンドプロンプトを管理者権限で開き、最初に次のコマンドで WSL を更新する。

```powershell
wsl --update
```

更新が完了した後、次のコマンドで WSL 上に Kali Linux をインストールする。

```powershell
wsl --install -d kali-linux
```

更新またはインストール時に再起動を求められた場合は、Windows を再起動してから次の操作に進む。詳しくは [Microsoft の WSL 基本コマンド](https://learn.microsoft.com/ja-jp/windows/wsl/basic-commands) と [WSL インストール手順](https://learn.microsoft.com/ja-jp/windows/wsl/install) を参照する。

Kali Linux の初回起動時に、Linux 用のユーザー名とパスワードを作成してから次の手順に進む。詳しくは、後述の「補足：Kali Linux の初期設定と手動での環境構築」を参照する。

### 2. リポジトリをクローンする

Git が未インストールの場合は、Kali Linux のターミナルで先に次のコマンドを実行する。

```bash
sudo apt update
sudo apt install -y git
```

本リポジトリを `~/temp/sus_BC2` にクローンする。

```bash
mkdir -p ~/temp
cd ~/temp
git clone https://github.com/yanagihalab/sus_BC2
cd sus_BC2
```

関連する環境構築スクリプト: `./setup/normal/01-create-workdir-and-python-env.sh`（クローンと Python 仮想環境の作成を行う）。

### 3. 環境構築スクリプトを実行する

リポジトリのディレクトリへ移動し、実験用の環境構築スクリプトを実行する。
本書で紹介する環境構築スクリプトのコマンドは、特に指定がない限り、リポジトリルートから実行する。

```bash
cd ~/temp/sus_BC2
./setup/normal/wsl-kali-experiment-env.sh
```

このスクリプトは、Kali Linux の更新、基本ツールのインストール、Python 仮想環境の作成、Python ライブラリのインストール、Proposer Visualizer の依存パッケージのインストールをまとめて行う。
SimBlock、`injectived`、Docker などの環境構築は、後述の各項目を参照する。

<details>
<summary>補足：Kali Linux の初期設定と手動での環境構築</summary>

Kali Linux の初期設定と、更新・基本ツールのインストールを個別に行う場合の手順を以下に示す。
更新と基本ツールのインストールは、主手順 3 の環境構築スクリプトで実行されるため、スクリプトを使用する場合は手動で行う必要はない。

#### Kali Linux の初期設定

インストール後に Kali Linux が起動したら、Linux 用のユーザー名とパスワードを作成する。
パスワードの入力中は画面に文字が表示されないが、実際には入力されている。
この初回設定は、環境構築スクリプトを実行する前に済ませる。

#### Kali Linux の更新

Kali Linux のターミナルで、次のコマンドを実行する。

```bash
sudo apt update
sudo apt upgrade -y
```

#### 基本ツールのインストール

Kali Linux 内に、Python、Git、Java、unzip、npm、jq などをインストールする。

```bash
sudo apt install -y python3-pip python3-venv openjdk-11-jdk unzip npm jq git curl nodejs
```

インストール後、各ツールのバージョンを確認する。

```bash
python3 --version
git --version
java -version
node --version
npm --version
jq --version
```

更新と基本ツールのインストールに対応する環境構築スクリプト: `./setup/normal/00-install-kali-packages.sh`（主手順 3 のスクリプトから呼び出される）。

</details>

## VS Code から Kali Linux を開く

VS Code から Kali Linux 内のファイルを編集する場合は、通常 `Remote - WSL` を利用する。
SSH 接続として追加したい場合は、`Remote - SSH` を利用する。

### Remote - WSL で開く

VS Code に WSL 拡張機能をインストールし、Kali Linux に接続する。
Kali Linux のターミナルから直接 VS Code を開く場合は、リポジトリのディレクトリで次のコマンドを実行する。

```bash
cd ~/temp/sus_BC2
code .
```

## Python 仮想環境の利用

主手順 3 で作成した Python 仮想環境を、現在のシェルで有効にする。

```bash
cd ~/temp/sus_BC2
source venv/bin/activate
```

環境構築スクリプトを使わずに手動で準備する場合は、リポジトリをクローンした後、次のコマンドで仮想環境を作成し、必要なライブラリをインストールする。

```bash
cd ~/temp/sus_BC2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

対応する環境構築スクリプト: `./setup/normal/01-create-workdir-and-python-env.sh`

一部の Python ファイルには、`*__*` のような未記入箇所がある。
対象チェーン、入力ファイル、試行回数、バリデータ数、ブロック数などを、実験条件に合わせて補完してから実行する。
未記入箇所が残っていると、構文エラーなどが発生することがある。

以降、各 Python スクリプトは、特に指定がない限り、仮想環境を有効にした状態でリポジトリルートから個別に実行する。
次のコマンドは各日の実行例である。

```bash
cd ~/temp/sus_BC2
python3 Day1/1-1_block-fetch.py
python3 Day2/2-1mm1_queue.py
python3 Day3/3-1_btc_mining.py
```

## SimBlock の実行環境の構築

SimBlock は Day3 で使用する。
SimBlock のビルドと実行には、Java 開発環境（JDK）が必要である。
本実験では、SimBlock に付属する Gradle Wrapper を用いてビルドおよび実行を行う。
必要なパッケージをインストールした後、SimBlock をクローンして実行する。

```bash
sudo apt update
sudo apt install -y openjdk-11-jdk unzip git
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

上記の `JAVA_HOME` は x86_64 環境の例である。環境に応じて、Java 11 のインストール先に変更する。

対応する環境構築スクリプト: `./setup/normal/03-install-simblock.sh`（ビルドまで行う。実行も行う場合は `RUN_SIMBLOCK=yes` を指定する）。

## injectived の導入・ウォレットの作成・送金

`injectived` の導入、ウォレットの作成、Faucet の利用、残高確認、送金（`bank send`）の手順は、次の README を参照する。

- [injectived README](scripts/injectived/README.md)

`injectived` 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

## TokenFactory / MTK の実行

TokenFactory を用いた MTK の作成、メタデータの設定、ミント（発行）、送金の手順と確認事項は、次の README を参照する。

- [TokenFactory MTK README](scripts/tokenfactory/README.md)

TokenFactory 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

## Proposer Visualizer の環境構築

Proposer Visualizer は、Day1 の実験で作成した提案者の系列（proposer sequence）を CSV ファイルから読み込み、ブラウザで可視化する Vite + React アプリである。
このアプリを使うには、Python とは別に Node.js と npm が必要である。

```bash
cd ~/temp/sus_BC2
sudo apt install -y nodejs npm
cd Day1/Proposer-visualizer
npm install
npm run start
```

対応する環境構築スクリプト: `RUN_VISUALIZER=yes ./setup/normal/08-setup-proposer-visualizer.sh`

`npm run start` は `public/out/` または `out/` 配下の CSV ファイルを列挙し、起動時に通常は同じディレクトリに `index.json`（マニフェスト）を生成してから Vite 開発サーバーを起動する。
起動後、ターミナルに表示される URL をブラウザで開く。
通常は `http://localhost:5173` で確認できる。

マニフェストを生成済みの場合は、次のコマンドで Vite 開発サーバーのみを起動することもできる。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
npm run dev -- --host 0.0.0.0
```

依存関係に問題がある場合は、`node_modules/` と `package-lock.json` を削除して依存パッケージを再インストールする。
`node_modules/`、ビルド出力、生成されたマニフェストは Git の管理対象外である。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
rm -rf node_modules package-lock.json
npm install
```

対応する環境構築スクリプト: `RESET_NODE_MODULES=yes ./setup/normal/08-setup-proposer-visualizer.sh`

## CW20 コントラクト用の Docker / CosmWasm 環境の構築と実行

CW20 コントラクト用の Docker / CosmWasm 環境の構築、WASM のビルド、コードの登録（`store`）、コントラクトの初期化（`instantiate`）、照会（`query`）、送金（`transfer`）、ミント（`mint`）の手順は、次の README を参照する。

- [CW20 README](scripts/CW20/README.md)

CW20 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
```

初期化メッセージ（instantiate message）は、次のシェルスクリプトで作成する。

```bash
cd ~/temp/sus_BC2
source scripts/CW20/load-env.sh
scripts/CW20/create-instantiate-msg.sh
```

## 困ったとき

### `python` コマンドが見つからない

環境によっては `python` ではなく `python3` を使う。

```bash
cd ~/temp/sus_BC2
python3 Day1/1-1_block-fetch.py
```

### ライブラリが見つからない

仮想環境を有効にしてから、必要なライブラリを再インストールする。

```bash
cd ~/temp/sus_BC2
source venv/bin/activate
pip install -r requirements.txt
```

### `*__*` のエラーが出る

実行した Python ファイルに、未記入箇所が残っている可能性がある。
ファイルを開いて `*__*` を探し、実験条件に合わせて補完する。

### SSH 接続できない

WSL を再起動した後に SSH 接続できない場合は、Kali Linux 側で SSH サーバーを再起動する。

```bash
sudo service ssh restart
```

関連する環境構築スクリプト: `./setup/normal/02-setup-vscode-ssh.sh`

## 補足

- [requirements.txt](requirements.txt) には、実験で使用する Python ライブラリを記載している。
- [docs/injective-setup.md](docs/injective-setup.md) には、環境構築や実験で使用するコマンド例を記載している。
- 秘密鍵、ニーモニック、個人用 RPC 認証情報などはコミットしないこと。

## Kali Linux を WSL から登録解除する場合

Kali Linux の WSL 環境を削除して作り直す場合は、Windows のコマンドプロンプトで次のコマンドを実行する。
この操作を行うと、Kali Linux 内のファイル、設定、インストール済みパッケージが削除される。
必要なファイルは事前に退避する。

先に次のコマンドで、削除するディストリビューションの登録名を確認する。

```cmd
wsl --list --verbose
```

削除するディストリビューションの登録名を確認した後、次のコマンドで登録を解除する。

```cmd
wsl --unregister kali-linux
```

<!-- ## MacBook ユーザー向けの補足

MacBook 上で作業する場合は、Docker Desktop を利用して Kali Linux ベースの実験環境イメージを作成し、README、`./setup/normal/`、`./setup/macbook/` の最小検証を行う。
MacBook 向けの Docker 環境構築と、WSL / Kali Linux の通常実験環境構築は、フォルダと入口スクリプトを分けている。

### MacBook 用入口スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/macbook/macbook-docker-env.sh` | MacBook 上の Docker Desktop で Kali Linux ベースの実験環境イメージを作成し、基本検証を行う |

MacBook では次を実行する。

```bash
cd ~/temp/sus_BC2
./setup/macbook/macbook-docker-env.sh
```

対応する環境構築スクリプト: `./setup/macbook/macbook-docker-env.sh`

### MacBook 用スクリプト

| ファイル | 内容 |
| --- | --- |
| `./setup/macbook/verify-in-docker.sh` | README、`./setup/normal/`、`./setup/macbook/` の最小 Docker 検証 |

MacBook で各環境構築スクリプトを実行する場合は、`./setup/macbook/00-install-kali-packages.sh` から `./setup/macbook/11-store-cw20-code.sh` までの同名ラッパースクリプトを使う。
これらは `./setup/normal/` の本体を呼び出す入口である。

MacBook 上で Docker による簡易検証を行う場合は、[MacBook ユーザー向け: Docker による動作確認](docs/macbook-docker-verification.md) を参照する。 -->
