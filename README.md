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

Kali Linux の初回起動時に、Linux 用のユーザー名とパスワードを作成してから次の手順に進む。詳しくは、後述の「補足：初期設定と一括セットアップの内容」を参照する。

### 2. リポジトリをクローンする

Git が未インストールの場合は、Kali Linux のターミナルで先に次のコマンドを実行する。
これはリポジトリ取得前の準備であり、取得後の環境構築は手順 3 のスクリプトで行う。

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

### 3. 環境構築スクリプトを実行する

リポジトリルートで、次のコマンドを実行する。

```bash
cd ~/temp/sus_BC2
./setup/normal/wsl-kali-experiment-env.sh
```

このスクリプトを実行すると、標準設定ではリポジトリルートに `venv` という名前の Python 仮想環境（`~/temp/sus_BC2/venv/`）が作成され、必要なライブラリがインストールされる。

<details>
<summary>補足：一括セットアップの処理順序</summary>

`wsl-kali-experiment-env.sh` は、次の順序で処理を実行する。標準設定では SSH サーバーの設定以外をすべて行う。
各処理のコマンドと役割は、次の「補足：初期設定と一括セットアップの内容」を参照する。

| 順序 | 処理 | 内容 |
| --- | --- | --- |
| 1 | 設定・実行条件の確認 | 各 `SETUP_*` の値、リポジトリ、`requirements.txt`、Visualizer の `package.json` を確認する。Injective を導入する場合は x86_64 が必要で、CW20 をビルドする場合は Docker の導入も有効にする。作業先と各パスを設定し、WSL 上での実行かを確認する。WSL ではない場合は警告を表示する。 |
| 2 | Kali の更新と基本ツールの導入 | `00-install-kali-packages.sh` で、APT のパッケージ一覧更新、インストール済みパッケージの更新、基本ツールの導入を順に行う。Python 用ツール、Java 11、Node.js、npm、Git、curl、unzip、jq を導入し、Node.js が 20 以上であることと各ツールのバージョンを確認する。この段階の APT 処理にはダウンロードの再試行設定が入っている。 |
| 3 | Python 仮想環境の作成 | リポジトリ直下に `venv/` を作成し、その環境に `requirements.txt` の `requests`、`numpy`、`scipy`、`tqdm`、`pandas`、`matplotlib` を導入する。作成先は `VENV_DIR` で変更できる。 |
| 4 | Visualizer の依存パッケージの導入 | `08-setup-proposer-visualizer.sh` で、`Day1/Proposer-visualizer` 内の `npm install` を実行する。Visualizer の起動は別途行う。 |
| 5 | SSH サーバーの設定（任意） | `SETUP_SSH=yes` の場合だけ、`02-setup-vscode-ssh.sh` を実行する。OpenSSH を導入し、標準ポートを `2222` に設定する。パスワード認証を有効、root ログインを無効にし、SSH サービスを再起動する。 |
| 6 | SimBlock の取得とビルド | `03-install-simblock.sh` で依存パッケージを導入し、SimBlock のリポジトリがなければ取得する。Java 11 の JDK を選択し、Gradle の `clean` と `build` を実行する。シミュレーションの実行は別途行う。 |
| 7 | injectived の導入 | `04-install-injectived.sh` で Linux amd64 向けの配布ファイルを取得・展開し、`injectived` を `/usr/local/bin/` に配置する。共有ライブラリが同梱されている場合は `/usr/lib/` に配置し、最後にバージョンを確認する。 |
| 8 | Docker Engine の導入と起動 | `09-install-docker.sh` で `docker.io` を導入し、Docker サービスを起動してバージョンを確認する。標準設定では Docker グループへのユーザー追加を省略し、`hello-world` も実行しない。 |
| 9 | CW20 サンプルの WASM ビルド | `10-build-cw20-sample.sh` で Docker への接続を確認し、必要に応じて `sudo docker` を使う。`cw-plus` のリポジトリがなければ取得し、`cosmwasm/workspace-optimizer:0.17.0` でビルドする。生成された `cw-plus/artifacts/cw20_base.wasm` を確認する。 |
| 10 | 完了メッセージと操作方法の表示 | リポジトリ、仮想環境、外部リポジトリ・ダウンロードの保存先を表示し、仮想環境を有効にするコマンドや、SSH 設定・各機能の省略方法を案内する。標準の外部リポジトリ・ダウンロード先はリポジトリの親ディレクトリ（本書の配置では `~/temp`）である。 |

Visualizer、SimBlock、Injective、Docker、CW20 は、対応する `SETUP_*` に `no` を指定すると省略できる。Docker を省略する場合は `SETUP_DOCKER=no SETUP_CW20=no` を指定する。
主要な導入・ビルド処理が失敗すると、後続の処理を実行せず停止する。途中までの変更は自動では巻き戻さない。

仮想環境は自動作成されるが、現在のターミナルで有効にするには、完了後に次を実行する。

```bash
cd ~/temp/sus_BC2
source venv/bin/activate
```

WSL 本体の更新と Kali Linux のインストールは、スクリプト実行前に Windows 側で行う。
ウォレット作成、送金、TokenFactory の操作、CW20 のチェーンへの登録・初期化は、一括セットアップ後の実験手順で行う。

</details>

<details>
<summary>補足：初期設定と一括セットアップの内容</summary>

#### 一括セットアップの対象と処理内容

標準セットアップは x86_64 版 Kali Linux を対象とする。`injectived` には Linux amd64 向けの配布バイナリを使用する。
本書で紹介する環境構築スクリプトのコマンドは、特に指定がない限り、リポジトリルートから実行する。
環境構築は、このスクリプトの実行に集約している。標準の設定で、次の処理を順に行う。
以下の補足では、スクリプト内で実行するコマンドとその役割を示す。通常の準備には主手順 3 を使い、補足は各処理を理解するために参照する。
コマンド例は、リポジトリを `~/temp/sus_BC2` に配置した場合の標準パスで記載している。`WORKDIR`、`VENV_DIR`、`APP_DIR` などを変更した場合は、指定したパスに読み替える。
一括セットアップは `set -euo pipefail` により、主要な処理の失敗や未設定変数の参照を検出して停止する。以下のコードブロックは、処理ごとの説明である。

| 対象 | セットアップ内容 |
| --- | --- |
| Kali Linux | パッケージ情報・インストール済みパッケージの更新 |
| 基本ツール | Python、Java 11、Node.js、npm、Git、curl、unzip、jq などの導入 |
| Python | `venv` という名前の仮想環境の作成と `requirements.txt` のライブラリの導入 |
| Proposer Visualizer | Node.js 20 以降の確認と npm 依存パッケージの導入 |
| SimBlock | ソースコードの取得と Java 11 によるビルド |
| injectived | CLI と共有ライブラリの導入 |
| Docker / CW20 | Docker の導入・起動、CW20 サンプルの取得と WASM のビルド |

完了後は、後述の各項目に従って仮想環境の有効化、アプリの起動、実験を行う。

#### Kali Linux の初期設定

インストール後に Kali Linux が起動したら、Linux 用のユーザー名とパスワードを作成する。
パスワードの入力中は画面に文字が表示されないが、実際には入力されている。
この初回設定は、環境構築スクリプトを実行する前に済ませる。

#### Kali Linux の更新

一括セットアップでは、次のコマンドを実行する。

```bash
sudo apt-get --error-on=any -o Acquire::Retries=5 update
sudo apt-get -o Acquire::Retries=5 --with-new-pkgs upgrade -y
```

`apt-get update` は、利用可能なパッケージとバージョンの一覧を更新する。`--error-on=any` は、更新中にエラーがあった場合に失敗として扱う指定である。
`apt-get upgrade` は、その一覧を使ってインストール済みパッケージを更新する。`--with-new-pkgs` は更新に必要な新規パッケージの導入を許可し、`-y` は確認への応答を自動化する。
`-o Acquire::Retries=5` は、このコマンドのダウンロード再試行回数を 5 回に設定する。
`00-install-kali-packages.sh` 内の APT 処理が失敗した場合は、元の出力に加えて処理段階、スクリプトと行番号、実行コマンド、終了コードを表示し、後続の処理を停止する。

#### 基本ツールのインストール

基本ツールは、次のコマンドでインストールする。

```bash
sudo apt-get -o Acquire::Retries=5 install -y \
  python3-pip python3-venv openjdk-11-jdk \
  unzip npm jq git curl nodejs
```

| パッケージ | 用途 |
| --- | --- |
| `python3-pip` / `python3-venv` | Python ライブラリの管理と仮想環境の作成 |
| `openjdk-11-jdk` | SimBlock のビルドと実行 |
| `nodejs` / `npm` | Visualizer の依存パッケージの導入と起動 |
| `git` / `curl` / `unzip` | ソースコード・配布ファイルの取得と展開 |
| `jq` | JSON の表示・確認 |

スクリプトは Node.js のメジャーバージョンを確認し、20 未満の場合は停止する。
導入後、次のコマンドで各ツールのバージョンを確認する。

```bash
python3 --version
git --version
java -version
node --version
npm --version
jq --version
```

#### Python 仮想環境（venv）の作成と利用

`venv` は、実験で使う Python とライブラリをプロジェクトごとに管理するための仮想環境である。
`wsl-kali-experiment-env.sh` を実行すると、標準設定でリポジトリ内の `venv/` にこの環境が自動作成される。[Python の venv ドキュメント](https://docs.python.org/ja/3/library/venv.html) も参照できる。

```bash
cd ~/temp/sus_BC2
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

`python3 -m venv venv` は、Python に付属する `venv` モジュールを使い、最後の引数で指定した `venv/` ディレクトリに仮想環境を作成する。
作成後は、`venv/bin/python` がこの環境の Python 実行ファイルとなる。

`venv/bin/python -m pip install -r requirements.txt` は、仮想環境の Python で `pip` を実行し、`requirements.txt` に記載されたライブラリをその環境へインストールする。
一括セットアップも、このように仮想環境の Python を直接指定してライブラリを導入する。

実験を始めるときは、現在のターミナルで仮想環境を有効にする。

```bash
cd ~/temp/sus_BC2
source venv/bin/activate
python --version
python -m pip list
```

`source venv/bin/activate` は、現在のシェルの `PATH` を変更し、`python` や `pip` が仮想環境内の実行ファイルを参照するようにする。
スクリプトの子プロセス内の設定は、実行元のターミナルには引き継がれないため、一括セットアップ後にもこの有効化が必要である。
`python -m pip list` は、仮想環境にインストールされたライブラリを確認するコマンドである。

実験を終えて仮想環境の利用を解除するときは、次を実行する。作成した `venv/` は残るため、次回も `source` で有効化できる。

```bash
deactivate
```

#### Proposer Visualizer の依存パッケージの導入

Node.js と npm を導入した後、アプリのディレクトリで次を実行する。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
npm install
```

`npm install` は、`package.json` とロックファイルに基づいて必要なパッケージを `node_modules/` に導入する。
一括セットアップは依存パッケージの準備までを行い、アプリの起動は後述の `npm run start` で行う。
`RESET_NODE_MODULES=yes` を指定した場合だけ、インストール前に次の削除処理を行い、依存パッケージとロックファイルを作り直す。

```bash
rm -rf node_modules package-lock.json
```

#### SimBlock の取得とビルド

Java 11 と取得に必要なツールを確認し、SimBlock のリポジトリがない場合にクローンする。

```bash
sudo apt update
sudo apt install -y openjdk-11-jdk unzip git
mkdir -p ~/temp
if [ ! -d ~/temp/simblock/.git ]; then
  git clone https://github.com/dsg-titech/simblock ~/temp/simblock
fi
```

`.git` の存在確認は、取得済みのソースコードを再度クローンしないための処理である。
次に、Java 11 の JDK を選ぶ。既存の `JAVA_HOME` が Java 11 の JDK を指している場合はその値を使い、それ以外はインストール先から選び直す。
`java` と `javac` の存在、および Java のバージョンを確認する処理は次のとおりである。

```bash
is_java11_jdk() {
  local jdk_dir="$1"
  local version
  [ -n "$jdk_dir" ] && [ -x "$jdk_dir/bin/java" ] && [ -x "$jdk_dir/bin/javac" ] || return 1
  version="$("$jdk_dir/bin/java" -version 2>&1)" || return 1
  [[ "$version" == *'version "11.'* || "$version" == *'version "11"'* ]]
}

if ! is_java11_jdk "${JAVA_HOME:-}"; then
  JAVA_HOME=""
  while IFS= read -r candidate; do
    if is_java11_jdk "$candidate"; then
      JAVA_HOME="$candidate"
      break
    fi
  done < <(find /usr/lib/jvm -maxdepth 1 -type d -name 'java-11-openjdk-*' | sort)
fi

if [ -z "$JAVA_HOME" ]; then
  echo "Java 11 JDK が見つかりません" >&2
  exit 1
fi

export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"
cd ~/temp/simblock
chmod +x gradlew
./gradlew clean
./gradlew build
```

`JAVA_HOME` は使用する JDK の場所を指定し、`PATH` の先頭へその `bin/` を追加することで Java 11 を選択する。
`chmod +x gradlew` は Gradle Wrapper に実行権限を付ける。
`clean` は前回のビルド出力を削除し、`build` はソースコードをビルドする。
SimBlock のシミュレーション実行は、後述の `./gradlew :simulator:run` で行う。

#### injectived の導入

Linux amd64 向けの配布ファイルを取得し、CLI と共有ライブラリを配置する。

```bash
sudo apt update
sudo apt install -y wget unzip
mkdir -p ~/temp
cd ~/temp
wget -O linux-amd64.zip https://github.com/InjectiveFoundation/injective-core/releases/latest/download/linux-amd64.zip
unzip -o linux-amd64.zip
chmod +x injectived
sudo mv injectived /usr/local/bin/
if [ -f libwasmvm.x86_64.so ]; then
  sudo mv libwasmvm.x86_64.so /usr/lib/
  sudo ldconfig
fi
injectived version
```

`wget -O` は保存するファイル名を指定してダウンロードし、`unzip -o` は既存ファイルを上書きして展開する。
`/usr/local/bin/` は CLI の配置先である。共有ライブラリが同梱されている場合は `/usr/lib/` に配置し、`ldconfig` でライブラリの検索情報を更新する。
最後に `injectived version` で起動できることを確認する。

#### Docker の導入と起動

Docker Engine をインストールし、サービスを起動する。

```bash
sudo apt update
sudo apt install -y docker.io
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl enable docker || true
  sudo systemctl start docker || sudo service docker start
else
  sudo service docker start
fi
sudo docker --version
```

`systemctl enable` はサービスの自動起動を設定し、`systemctl start` は現在のサービスを起動する。
`systemctl` が使えない場合や起動に失敗した場合は、`service docker start` で起動する。
`ADD_USER_TO_DOCKER_GROUP=yes` を指定した場合だけ、次のコマンドで現在のユーザーを Docker グループへ追加する。

```bash
sudo usermod -aG docker "$USER"
```

グループ変更は、新しいシェルを開くか `newgrp docker` を実行して反映する。
CW20 のビルドでは、通常の Docker アクセスが使えない場合に `sudo docker` を選ぶため、標準セットアップの途中でグループ変更を反映する操作は不要である。

#### CW20 サンプルの取得と WASM のビルド

ビルド用の Docker を通常の権限で使えるか確認し、必要に応じて `sudo` で実行する。

```bash
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker がインストールされていません" >&2
  exit 1
fi
DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
    DOCKER=(sudo docker)
  else
    echo "Docker Engine に接続できません" >&2
    exit 1
  fi
fi

mkdir -p ~/temp
if [ ! -d ~/temp/cw-plus/.git ]; then
  git clone https://github.com/CosmWasm/cw-plus.git ~/temp/cw-plus
fi
cd ~/temp/cw-plus
ls contracts/cw20-base
"${DOCKER[@]}" run --rm \
  -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/code/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/workspace-optimizer:0.17.0
ls -lh artifacts/
ls -lh artifacts/cw20_base.wasm
```

`docker info` は Docker Engine への接続確認である。
`docker run --rm` はビルド用コンテナを起動し、終了時にコンテナを削除する。
`-v` は `cw-plus` のルートをコンテナ内の `/code` に対応させ、2つの `--mount` は中間ビルド成果物（`target/`）と取得した Rust パッケージのキャッシュを保持する。
optimizer はワークスペース全体をビルドし、`artifacts/cw20_base.wasm` などを生成する。`ls -lh` は生成ファイルとサイズの確認に使う。

#### VS Code を SSH で接続する場合

通常は Remote - WSL を使用する。Remote - SSH を使用する場合は、一括セットアップ時に `SETUP_SSH=yes` を指定する。

```bash
cd ~/temp/sus_BC2
SETUP_SSH=yes ./setup/normal/wsl-kali-experiment-env.sh
```

この指定で実行される SSH サーバーの導入と設定は次のとおりである。

```bash
sudo apt update
sudo apt install -y openssh-server
PORT="${PORT:-2222}"
SSHD_CONFIG="/etc/ssh/sshd_config"
sudo cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

set_config() {
  local key="$1"
  local value="$2"
  if sudo grep -Eq "^[#[:space:]]*${key}[[:space:]]+" "$SSHD_CONFIG"; then
    sudo sed -i -E "s|^[#[:space:]]*${key}[[:space:]]+.*|${key} ${value}|" "$SSHD_CONFIG"
  else
    printf '%s %s\n' "$key" "$value" | sudo tee -a "$SSHD_CONFIG" >/dev/null
  fi
}

set_config "Port" "$PORT"
set_config "PasswordAuthentication" "yes"
set_config "PermitRootLogin" "no"
sudo service ssh restart
```

`cp` は変更前の設定を日時付きで保存する。`set_config` は既存の設定行を置換し、該当行がなければ追記する。
標準ポートは `2222` で、パスワード認証を有効にし、root のログインを無効にする。
`service ssh restart` は設定を反映するために SSH サーバーを再起動する。

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

## SimBlock の実行

SimBlock は Day3 で使用する。ソースコードの取得とビルドは、主手順 3 の一括セットアップで完了する。
実験時は、現在のターミナルで Java 11 を選び、SimBlock に付属する Gradle Wrapper で実行する。

```bash
export JAVA_HOME="$(find /usr/lib/jvm -maxdepth 1 -type d -name 'java-11-openjdk-*' | sort | head -n 1)"
export PATH="$JAVA_HOME/bin:$PATH"
cd ~/temp/simblock
./gradlew :simulator:run
```

## injectived の導入・ウォレットの作成・送金

`injectived` の導入は、主手順 3 の一括セットアップで完了する。
ウォレットの作成と送金（`bank send`）には、次のスクリプトを使用する。

| 操作 | スクリプト |
| --- | --- |
| ウォレットの作成・確認 | [create-test-wallet.sh](scripts/injectived/create-test-wallet.sh) |
| INJ の送金 | [bank-send.sh](scripts/injectived/bank-send.sh) |

`injectived` 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/injectived/load-env.sh
```

<details>
<summary>補足：環境変数の読み込みとウォレット作成のコマンド</summary>

#### 環境変数の設定

`load-env.sh` は `source` で読み込み、現在のシェルに `export` で値を設定する。
`${変数:-既定値}` は、変数が未設定または空の場合に既定値を使う指定である。すでに設定した値は保持される。
Injective 用の設定処理は次のとおりである。

```bash
export KEY_NAME="${KEY_NAME:-testwallet}"
export CHAIN_ID="${CHAIN_ID:-injective-888}"
export NODE="${NODE:-https://injective-testnet-rpc.publicnode.com:443}"
export GAS_PRICES="${GAS_PRICES:-500000000inj}"
export GAS="${GAS:-1000000}"
export BANK_SEND_GAS="${BANK_SEND_GAS:-200000}"
export AMOUNT="${AMOUNT:-100000000inj}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export KEYRING_BACKEND="${KEYRING_BACKEND:-test}"

if command -v injectived >/dev/null 2>&1; then
  export MY_ADDR="${MY_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export MY_ADDR="${MY_ADDR:-}"
fi
export ADDR="${ADDR:-$MY_ADDR}"
```

`KEY_NAME` は使用する鍵の名前、`CHAIN_ID` と `NODE` は接続先、`GAS_PRICES` はガス単価である。
`GAS` はガス上限、`BANK_SEND_GAS` は INJ 送金用のガス上限、`AMOUNT` は送金量、`RECIPIENT_ADDR` は送金先を表す。
`KEYRING_BACKEND` は鍵の保存方式を指定する。`keys show -a` は、鍵に対応するアドレスを取得する。
鍵がまだない場合、アドレスは空のままとなるため、作成後に取得する。

#### ウォレットの作成とアドレス取得

`create-test-wallet.sh` は、同じ名前の鍵が存在するか確認し、未作成の場合だけウォレットを作成する。

```bash
if ! injectived keys show "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND" >/dev/null 2>&1; then
  injectived keys add "$KEY_NAME" --keyring-backend "$KEYRING_BACKEND"
else
  echo "Wallet already exists: $KEY_NAME"
fi
MY_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
```

`keys add` は鍵とウォレットを作成する。作成後の `MY_ADDR` を Faucet や残高照会に使用する。
この手動例では現在のシェルにアドレスが設定される。補助スクリプトを実行した場合は、表示される案内に従って環境変数を読み込む。

</details>

ウォレット作成後、[Injective testnet の Faucet](https://cloud.google.com/application/web3/faucet/injective/testnet) で INJ を取得し、残高を確認する。

```bash
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

送金時は `RECIPIENT_ADDR` と `AMOUNT` を設定し、`CONFIRM_SEND=yes` を指定して `bank-send.sh` を実行する。

<details>
<summary>補足：bank-send.sh が実行する送金コマンド</summary>

送信元の鍵、送金先、送金量を指定して、次のコマンドを実行する。例の送金先は実際のアドレスに置き換える。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
AMOUNT="100000000inj"
BANK_SEND_GAS="${BANK_SEND_GAS:-${GAS:-200000}}"
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "$AMOUNT" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$BANK_SEND_GAS" \
  --broadcast-mode sync \
  -y
```

`--from` は署名に使う鍵、`--chain-id` と `--node` は接続先を指定する。
`--gas-prices` と `--gas` は手数料計算に使う設定である。送金には `BANK_SEND_GAS` を使う。
`--broadcast-mode sync` はトランザクションを送信して応答を受け取る方式で、ブロックへの取り込み結果は TxHash で別途確認する。
`-y` は CLI の確認を自動承認する指定である。
`CONFIRM_SEND=yes` は補助スクリプト内の実行条件であり、直接 `injectived` を実行する場合のオプションではない。

</details>

### トランザクションの確認

送金、TokenFactory、CW20 などの書き込み操作で TxHash が返ったら、次のコマンドで結果を確認する。
ブロックに取り込まれ、`code` が `0` であることを確認する。

```bash
TXHASH="ここにTxHashを入れる"
injectived q tx "$TXHASH" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --output json | jq
```

## TokenFactory / MTK の実行

TokenFactory を用いた MTK の作成、メタデータの設定、ミント（発行）、残高確認、送金には、[07-tokenfactory-mtk.sh](setup/normal/07-tokenfactory-mtk.sh) を使用する。

TokenFactory 用の環境変数は、次のシェルスクリプトで現在のシェルに読み込む。

```bash
cd ~/temp/sus_BC2
source scripts/tokenfactory/load-env.sh
```

操作一覧は、次のコマンドで確認する。

```bash
./setup/normal/07-tokenfactory-mtk.sh help
```

`create-denom`、`set-metadata`、`mint`、`balance`、`send` の各操作を指定できる。
`create-denom` で denom を作成してから、メタデータ設定、ミント、送金へ進む。同じ denom の作成は一度だけ行う。
書き込み操作には `CONFIRM_TX=yes` と、作成手数料・ガス手数料を支払うための INJ 残高が必要である。
メタデータ設定の実行前に、補足の「メタデータの設定」に記載した CLI 引数の確認事項を参照する。

<details>
<summary>補足：TokenFactory の環境設定と各操作のコマンド</summary>

#### 環境変数と denom の組み立て

鍵名、チェーン、RPC、ガス単価、鍵の保存方式は Injective の共通設定と同じである。
TokenFactory 用の `load-env.sh` は、次の固有設定を読み込む。

```bash
export GAS="${GAS:-300000}"
export SUBDENOM="${SUBDENOM:-mtk}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
if command -v injectived >/dev/null 2>&1; then
  export CREATOR_ADDR="${CREATOR_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export CREATOR_ADDR="${CREATOR_ADDR:-}"
fi
if [ -n "$CREATOR_ADDR" ]; then
  export DENOM="${DENOM:-factory/${CREATOR_ADDR}/${SUBDENOM}}"
else
  export DENOM="${DENOM:-}"
fi
```

`CREATOR_ADDR` は作成者のアドレス、`SUBDENOM` はトークン名の末尾部分である。
完全な denom は `factory/作成者アドレス/subdenom` の形式になる。
補助スクリプトの各操作では、鍵からアドレスを取得し、denom を組み立て直す。
以下の手動例も、使用する鍵から値を取得する。ガス上限の例は `300000` とする。

```bash
GAS=300000
CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
DENOM="factory/${CREATOR_ADDR}/${SUBDENOM}"
```

`load-env.sh` は既存の `GAS` を保持するため、操作に合わせてガス値を指定する。
`07-tokenfactory-mtk.sh env` は設定を画面に表示する操作であり、現在のシェルへの読み込みは `source` で行う。

#### denom の作成

`create-denom` では、subdenom、名称、記号、小数桁数を指定する。

```bash
injectived tx tokenfactory create-denom \
  "$SUBDENOM" "My Token" "MTK" 6 \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

作成トランザクションの成功を確認してから、以降の操作へ進む。

#### メタデータの設定

名称、説明、表示単位などを登録する。以下は現在のスクリプトが使う引数を示したものである。

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
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

単位の JSON では、最小単位の exponent を `0`、表示単位 `MTK` の exponent を `6` としている。
現行スクリプトの末尾引数 `10 6` には、CLI の仕様との確認が必要である。
[公式の公開ソース v1.18.0](https://github.com/InjectiveFoundation/injective-core/blob/v1.18.0/injective-chain/modules/tokenfactory/client/cli/tx.go#L219-L267) では、末尾2引数は `decimals` と `shouldDisableAdminBurn` である。
この仕様で `10 6` を渡すと、小数桁数は `10`、管理者の burn の無効化は `false`（文字列 `true` の場合だけ有効）として扱われ、作成時と単位 JSON の `6` 桁設定に一致しない。
[公式のトークン作成ガイド](https://docs.injective.network/developers-defi/token-launch) には9引数の例もあるため、実行前に導入した CLI の引数を次のコマンドで確認する。

```bash
injectived tx tokenfactory set-denom-metadata --help
```

上記のコードブロックは現在のスクリプト内容を示したものであり、引数の修正方針は使用する CLI の仕様に合わせて決める。

#### ミント・残高確認・送金

ミントは、数量と denom を連結し、発行先のアドレスを指定する。

```bash
MINT_AMOUNT="${MINT_AMOUNT:-1000000000}"
injectived tx tokenfactory mint "${MINT_AMOUNT}${DENOM}" "$CREATOR_ADDR" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

`MINT_AMOUNT` は最小単位の数量で、変数自体には denom を含めない。
次のコマンドは、作成者の銀行残高を JSON で取得する。

```bash
injectived query bank balances "$CREATOR_ADDR" \
  --node="$NODE" --chain-id="$CHAIN_ID" -o json | jq
```

送金は、宛先と最小単位の数量を設定してから実行する。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
SEND_AMOUNT="${SEND_AMOUNT:-1000000}"
injectived tx bank send "$KEY_NAME" "$RECIPIENT_ADDR" "${SEND_AMOUNT}${DENOM}" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  -y
```

`CONFIRM_TX=yes` は補助スクリプト側の実行条件である。直接 CLI を使う場合は、上記のコマンドで処理を実行する。
各書き込み操作の結果は、返された TxHash で確認する。

</details>

## Proposer Visualizer の起動

Proposer Visualizer は、Day1 の実験で作成した提案者の系列（proposer sequence）を CSV ファイルから読み込み、ブラウザで可視化する Vite + React アプリである。
Node.js 20 以降、npm、アプリの依存パッケージは、主手順 3 の一括セットアップで導入済みとなる。
CSV ファイルは `Day1/Proposer-visualizer/out/` に配置する。サンプルとして `proposer_sequence.csv` を含めている。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
npm run start
```

`npm run start` は `public/out/` または `out/` 配下の CSV ファイルを列挙し、起動時に通常は同じディレクトリに `index.json`（マニフェスト）を生成してから Vite 開発サーバーを起動する。
起動後、ターミナルに表示される URL をブラウザで開く。
通常は `http://localhost:5173` で確認できる。

<details>
<summary>補足：Visualizer の起動時に実行するコマンド</summary>

`npm run start` は、マニフェストを生成する処理と、Vite 開発サーバーを起動する処理を順に実行する。
実際の処理をコマンドで表すと次のようになる。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
node scripts/gen-manifest.cjs &&
npm run dev -- --host 0.0.0.0 --port 5173
```

`node` は JavaScript のマニフェスト生成プログラムを実行する。
`&&` は前のコマンドが成功した場合だけ次を実行する指定である。
`--host 0.0.0.0` は WSL の外側からもアクセスできるように待受先を指定し、`--port 5173` は開発サーバーのポートを指定する。

</details>

マニフェストを生成済みの場合は、次のコマンドで Vite 開発サーバーのみを起動することもできる。

```bash
cd ~/temp/sus_BC2/Day1/Proposer-visualizer
npm run dev -- --host 0.0.0.0
```

`node_modules/`、ビルド出力、生成されたマニフェストは Git の管理対象外である。

## CW20 コントラクトの実行

Docker / CosmWasm 環境の構築と、CW20 サンプルの取得・WASM のビルドは、主手順 3 の一括セットアップで完了する。
生成された `~/temp/cw-plus/artifacts/cw20_base.wasm` をチェーンに登録するには、[11-store-cw20-code.sh](setup/normal/11-store-cw20-code.sh) を使用する。

コードの登録には `CONFIRM_TX=yes` を指定する。登録用のガス設定例は `GAS=3000000` である。

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

このスクリプトは `instantiate_msg.json` を生成する。
CW20 の symbol は英字またはハイフンの3〜12文字で指定する。TokenFactory の `factory/.../mtk` という denom は symbol として使用できない。

<details>
<summary>補足：CW20 の環境設定・コード登録・初期化・照会・送金・ミント</summary>

#### 環境変数とコード登録

CW20 用の `load-env.sh` は共通の鍵・接続設定に加え、次の保存先と操作用の変数を設定する。

```bash
export GAS="${GAS:-300000}"
export WORKDIR="${WORKDIR:-$HOME/temp}"
export CW_PLUS_DIR="${CW_PLUS_DIR:-$WORKDIR/cw-plus}"
export WASM_PATH="${WASM_PATH:-$CW_PLUS_DIR/artifacts/cw20_base.wasm}"
export CODE_ID="${CODE_ID:-}"
export CONTRACT_ADDR="${CONTRACT_ADDR:-}"
export RECIPIENT_ADDR="${RECIPIENT_ADDR:-}"
export CW20_SEND_AMOUNT="${CW20_SEND_AMOUNT:-1000000}"
export CW20_MINT_AMOUNT="${CW20_MINT_AMOUNT:-1000000}"
if command -v injectived >/dev/null 2>&1; then
  export SENDER_ADDR="${SENDER_ADDR:-$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND" 2>/dev/null || true)}"
else
  export SENDER_ADDR="${SENDER_ADDR:-}"
fi
export MY_ADDR="${MY_ADDR:-$SENDER_ADDR}"
```

`WASM_PATH` はビルド済みコードの保存先である。
`11-store-cw20-code.sh` は、このファイルの存在と `CONFIRM_TX=yes` を確認した後、次の登録コマンドを実行する。
以下の手動例では、コード登録用のガス上限を明示している。

```bash
GAS=3000000
injectived tx wasm store "$WASM_PATH" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS"
```

`store` は WASM コードをチェーンへ登録する操作で、成功後に code ID を取得できる。
このコマンドには `-y` がないため、CLI の確認に応答して実行する。
`CONFIRM_TX` は補助スクリプトの実行条件であり、直接 CLI を使う例では指定しない。

#### 初期化メッセージの作成

`create-instantiate-msg.sh` は、次の値を使って初期残高と minter を含む JSON を作成する。
`CREATOR_ADDR` が未設定の場合は、鍵からアドレスを取得する。

```bash
OUTPUT_FILE="${OUTPUT_FILE:-instantiate_msg.json}"
TOKEN_NAME="${TOKEN_NAME:-My Token}"
TOKEN_SYMBOL="${TOKEN_SYMBOL:-MTK}"
TOKEN_DECIMALS="${TOKEN_DECIMALS:-6}"
INITIAL_BALANCE="${INITIAL_BALANCE:-1000000}"
if ! echo "$TOKEN_SYMBOL" | grep -Eq '^[A-Za-z-]{3,12}$'; then
  echo "symbol は英字またはハイフンの3〜12文字で指定してください" >&2
  exit 1
fi
if [ -z "${CREATOR_ADDR:-}" ]; then
  CREATOR_ADDR="$(injectived keys show "$KEY_NAME" -a --keyring-backend "$KEYRING_BACKEND")"
fi

cat > "$OUTPUT_FILE" <<EOF
{
  "name": "$TOKEN_NAME",
  "symbol": "$TOKEN_SYMBOL",
  "decimals": $TOKEN_DECIMALS,
  "initial_balances": [
    {
      "address": "$CREATOR_ADDR",
      "amount": "$INITIAL_BALANCE"
    }
  ],
  "mint": {
    "minter": "$CREATOR_ADDR"
  },
  "marketing": null
}
EOF
jq . "$OUTPUT_FILE"
```

`cat > ... <<EOF` は、`EOF` までの内容を変数展開してファイルに書き出す。
`initial_balances` は初期残高の宛先と最小単位の数量、`mint.minter` は追加発行できるアドレスを指定する。
`jq .` は生成した JSON の構文と内容を確認する。

#### コントラクトの初期化

コード登録時の TxHash を使って「トランザクションの確認」のコマンドを実行し、結果の `events` から `code_id` を確認する。
取得した値を `CODE_ID` に設定し、初期化メッセージを使ってコントラクトを作成する。
以下では、コード登録用に設定したガス上限を、初期化・送金・ミントで使う設定例の `300000` に変更する。`source` は既存の `GAS` を保持するため、この変更を明示している。

```bash
GAS=300000
CODE_ID="取得したcode_id"
source scripts/CW20/load-env.sh
injectived tx wasm instantiate "$CODE_ID" "$(cat instantiate_msg.json)" \
  --from="$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id="$CHAIN_ID" \
  --node="$NODE" \
  --label "cw20-mtk-sample" \
  --no-admin \
  --gas-prices="$GAS_PRICES" \
  --gas="$GAS" \
  --output json \
  -y
```

初期化の TxHash で結果を確認し、`events` 内の `_contract_address` または `contract_address` の値を `CONTRACT_ADDR` に設定する。
`CODE_ID` は保存済みコードの番号、`CONTRACT_ADDR` は作成したコントラクトのアドレスであり、別の値である。

```bash
CONTRACT_ADDR="取得したcontract_address"
source scripts/CW20/load-env.sh
```

#### トークン情報と残高の照会

```bash
injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"token_info":{}}' \
  --node "$NODE" --output json | jq

injectived q wasm contract-state smart "$CONTRACT_ADDR" \
  '{"balance":{"address":"'"$SENDER_ADDR"'"}}' \
  --node "$NODE" --output json | jq
```

#### 送金

送金先と送金量を設定してから実行する。数量は最小単位で指定し、decimals が `6` の場合、`1000000` が `1 MTK` に相当する。

```bash
RECIPIENT_ADDR="inj1送金先アドレス"
CW20_SEND_AMOUNT="1000000"
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"transfer":{"recipient":"'"$RECIPIENT_ADDR"'","amount":"'"$CW20_SEND_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json \
  -y
```

#### ミント

初期化時に設定した minter の鍵を `KEY_NAME` に指定し、環境変数を読み込んでから実行する。

```bash
source scripts/CW20/load-env.sh
injectived tx wasm execute "$CONTRACT_ADDR" \
  '{"mint":{"recipient":"'"$SENDER_ADDR"'","amount":"'"$CW20_MINT_AMOUNT"'"}}' \
  --from "$KEY_NAME" \
  --keyring-backend "$KEYRING_BACKEND" \
  --chain-id "$CHAIN_ID" \
  --node "$NODE" \
  --gas-prices "$GAS_PRICES" \
  --gas "$GAS" \
  --output json \
  -y
```

送金・ミント後も、返された TxHash で結果を確認する。

</details>

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

### Visualizer の依存関係に問題がある

一括セットアップを `RESET_NODE_MODULES=yes` で再実行し、依存パッケージを入れ直す。

```bash
cd ~/temp/sus_BC2
RESET_NODE_MODULES=yes ./setup/normal/wsl-kali-experiment-env.sh
```

### `*__*` のエラーが出る

実行した Python ファイルに、未記入箇所が残っている可能性がある。
ファイルを開いて `*__*` を探し、実験条件に合わせて補完する。

### SSH 接続できない

WSL を再起動した後に SSH 接続できない場合は、Kali Linux 側で SSH サーバーを再起動する。

```bash
sudo service ssh restart
```

SSH サーバーの導入・設定には、一括セットアップを `SETUP_SSH=yes` で実行する。

## 補足

- [requirements.txt](requirements.txt) には、実験で使用する Python ライブラリを記載している。
- [docs/injective-setup.md](docs/injective-setup.md) には、過去の環境構築や実験で使用したコマンド例を記載している。
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
