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

<details>
<summary>補足：初期設定と一括セットアップの内容</summary>

#### 一括セットアップの対象と処理内容

標準セットアップは x86_64 版 Kali Linux を対象とする。`injectived` には Linux amd64 向けの配布バイナリを使用する。
本書で紹介する環境構築スクリプトのコマンドは、特に指定がない限り、リポジトリルートから実行する。
環境構築は、このスクリプトの実行に集約している。標準の設定で、次の処理を順に行う。

| 対象 | セットアップ内容 |
| --- | --- |
| Kali Linux | パッケージ情報・インストール済みパッケージの更新 |
| 基本ツール | Python、Java 11、Node.js、npm、Git、curl、unzip、jq などの導入 |
| Python | 仮想環境の作成と `requirements.txt` のライブラリの導入 |
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

パッケージ情報の更新と、インストール済みパッケージのアップグレードは、一括セットアップ内で行う。

#### 基本ツールのインストール

Node.js と npm を含む基本ツールのインストールも、一括セットアップ内で行う。
セットアップ完了後、各ツールのバージョンを確認できる。

```bash
python3 --version
git --version
java -version
node --version
npm --version
jq --version
```

#### VS Code を SSH で接続する場合

通常は Remote - WSL を使用する。Remote - SSH を使用する場合は、一括セットアップ時に `SETUP_SSH=yes` を指定する。

```bash
cd ~/temp/sus_BC2
SETUP_SSH=yes ./setup/normal/wsl-kali-experiment-env.sh
```

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

ウォレット作成後、[Injective testnet の Faucet](https://cloud.google.com/application/web3/faucet/injective/testnet) で INJ を取得し、残高を確認する。

```bash
injectived query bank balances "$MY_ADDR" --node="$NODE"
```

送金時は `RECIPIENT_ADDR` と `AMOUNT` を設定し、`CONFIRM_SEND=yes` を指定して `bank-send.sh` を実行する。

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
<summary>CW20 の初期化・照会・送金・ミント</summary>

#### コントラクトの初期化

コード登録時の TxHash を使って「トランザクションの確認」のコマンドを実行し、結果の `events` から `code_id` を確認する。
取得した値を `CODE_ID` に設定し、初期化メッセージを使ってコントラクトを作成する。

```bash
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
