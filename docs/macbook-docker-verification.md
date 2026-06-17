# MacBook ユーザー向け: Docker による動作確認

MacBook では WSL / Kali Linux をそのまま使えないため、Docker を使って Kali Linux コンテナ内で最低限の動作確認を行える。
この確認は、MacBook 上で README と `setup/` の基本的な整合性を確認するためのものである。
実際の Injective 送金、MTK mint、CW20 store など、チェーンへ書き込む操作は実行しない。

## 1. Docker Desktop を起動する

MacBook では、事前に Docker Desktop を起動しておく。
ターミナルで次のコマンドを実行し、Docker が使えることを確認する。

```bash
docker --version
docker info
```

`docker info` で Docker daemon へ接続できない場合は、Docker Desktop が起動しているか確認する。

## 2. Docker で検証する

リポジトリのルートディレクトリで次のコマンドを実行する。

```bash
./setup/macbook-docker-env.sh
```

このスクリプトは、MacBook 用の入口スクリプトである。
Kali Linux ベースの Docker image `sus-bc2-kali-env` を作成し、README と `setup/` の基本的な整合性を確認する。

image 名を変えたい場合は、`IMAGE_NAME` を指定する。

```bash
IMAGE_NAME=sus-bc2-kali-env-test ./setup/macbook-docker-env.sh
```

## 3. 検証内容

Docker コンテナ内では、次の内容を確認する。

- `setup/*.sh` の shell 構文に問題がないこと
- `requirements.txt` から Python 仮想環境を作成できること
- `setup/07-tokenfactory-mtk.sh help` が実行できること
- `setup/06-bank-send.sh` が、送金先未指定では送金を実行せず停止すること
- `setup/11-store-cw20-code.sh` が、WASM ファイル未作成では store を実行せず停止すること

## 4. 実行結果の例

検証に成功すると、次のように表示される。

```text
[1/5] Checking shell syntax
[2/5] Checking Python environment
[3/5] Checking MTK helper usage
[4/5] Checking bank send safety guard
[5/5] Checking CW20 store safety guard
MacBook Docker environment verification completed.
```

## 5. 注意点

Docker での確認は、MacBook ユーザーが手元で安全に確認するための簡易検証である。
WSL のインストール、VS Code Remote - WSL、実際の testnet 送金、Docker Engine の systemd 起動など、OS に強く依存する手順は Docker コンテナ内では完全には再現できない。
これらは README の各手順に従い、対象環境で個別に確認する必要がある。

## 6. 今回の MacBook Docker 検証結果

2026-06-17 に MacBook 上の Docker Desktop で確認した結果である。
検証では、通常の `kalilinux/kali-rolling` コンテナと、一部の amd64 専用バイナリ用に `--platform linux/amd64` を指定したコンテナを使った。

| 対象 | Docker 上の結果 |
| --- | --- |
| `setup/macbook-docker-env.sh` | 成功した。Kali Linux ベースの Docker image を作成し、Python 仮想環境と安全停止を確認した。 |
| `setup/wsl-kali-experiment-env.sh` | WSL / Kali Linux 実機向けのため、MacBook Docker では直接実行対象にしていない。部品スクリプトを個別に検証した。 |
| `setup/verify-in-docker.sh` | 成功した。README、`setup/`、shell 構文、送金系の安全停止を確認した。 |
| `setup/00-install-kali-packages.sh` | 成功した。Python、Git、Java、Node.js、npm、jq のバージョン表示まで確認した。 |
| `setup/01-create-workdir-and-python-env.sh` | 成功した。ローカル作業コピーから clone し、Python 仮想環境と `requirements.txt` の install を確認した。 |
| `setup/02-setup-vscode-ssh.sh` | 成功した。`openssh-server` を導入し、`sshd -t` と `service ssh status` で起動を確認した。 |
| `setup/03-install-simblock.sh` | 成功した。SimBlock を clone し、Java 11 の `JAVA_HOME` を自動検出して Gradle build まで確認した。 |
| `setup/04-install-injectived.sh` | `--platform linux/amd64` では成功した。通常の Apple Silicon arm64 コンテナでは、配布バイナリが amd64 のため実行できない。 |
| `setup/05-create-test-wallet.sh` | amd64 コンテナで成功した。検証用の一時 wallet を作成し、環境変数を表示できることを確認した。 |
| `setup/06-bank-send.sh` | 安全停止を確認した。`RECIPIENT_ADDR` や `CONFIRM_SEND=yes` が不足している場合、送金を実行せず停止した。 |
| `setup/07-tokenfactory-mtk.sh` | `help` と `env` を確認した。`env` は MTK 操作用の環境変数を表示する。書き込み操作は実行していない。 |
| `setup/08-setup-proposer-visualizer.sh` | 成功した。`npm install` と `npm run build` を確認した。 |
| `setup/09-install-docker.sh` | パッケージ導入までは進んだが、通常の Docker コンテナ内では Docker daemon の systemd 起動を完全には再現できなかった。WSL / Kali Linux 実機で確認する対象である。 |
| `setup/10-build-cw20-sample.sh` | 成功した。ホスト Docker socket をコンテナへ渡し、`cosmwasm/workspace-optimizer:0.17.0` で `cw20_base.wasm` の生成を確認した。 |
| `setup/11-store-cw20-code.sh` | 安全停止を確認した。WASM ファイルがない状態では store を実行せず停止した。実際の chain store は実行していない。 |

## 7. Apple Silicon での Injective 検証

`setup/04-install-injectived.sh` は、Injective 公式 release の `linux-amd64.zip` を取得する。
そのため、Apple Silicon MacBook の通常の arm64 Kali コンテナでは `injectived` を実行できない。
MacBook で `injectived` の導入から wallet 作成まで検証する場合は、amd64 コンテナを指定する。

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD:/work" \
  -w /work \
  kalilinux/kali-rolling \
  bash -lc 'WORKDIR=/tmp ./setup/04-install-injectived.sh && ./setup/05-create-test-wallet.sh'
```

このコマンドで表示される mnemonic は検証用の一時 wallet の秘密情報である。
本番用途や共有環境では使わないこと。

## 8. CW20 build を Docker で深く確認する場合

`setup/10-build-cw20-sample.sh` は、スクリプトの中でさらに `docker run` を実行する。
通常のコンテナでは内側の Docker から作業ディレクトリを参照できないため、ホスト Docker socket と、ホストにも存在する絶対パスを使う必要がある。

```bash
mkdir -p /private/tmp/sus_BC2-cwplus-verify

docker run --rm \
  -v "$PWD:$PWD" \
  -v /private/tmp/sus_BC2-cwplus-verify:/private/tmp/sus_BC2-cwplus-verify \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -w "$PWD" \
  kalilinux/kali-rolling \
  bash -lc 'apt update && apt install -y git docker-cli && WORKDIR=/private/tmp/sus_BC2-cwplus-verify ./setup/10-build-cw20-sample.sh'
```

成功すると、`artifacts/cw20_base.wasm` が表示される。
Apple Silicon では `cosmwasm/workspace-optimizer:0.17.0` が amd64 イメージとして動くため、エミュレーションにより時間がかかる場合がある。

## 9. 環境変数を表示するスクリプト

環境変数を設定するためのコマンドは、次の shell script にまとめている。
どちらも `export ...` 形式で表示するため、必要な行をターミナルに貼り付けて利用する。

- `setup/05-create-test-wallet.sh`: `CHAIN_ID`、`NODE`、`GAS_PRICES`、`GAS`、`KEY_NAME`、`MY_ADDR` を表示する。
- `setup/07-tokenfactory-mtk.sh env`: `KEY_NAME`、`CHAIN_ID`、`NODE`、`GAS_PRICES`、`GAS`、`SUBDENOM`、`CREATOR_ADDR`、`DENOM` を表示する。
