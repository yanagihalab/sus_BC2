承知した。
以後の README では、**元が Docker 環境であったことには触れず**、最初から **WSL + Kali Linux 上で構築する前提** の文面に統一すればよい。

以下に、**Docker への言及をすべて削除した最終版 README 全文** を示す。

````markdown
# 🌐 Web Visualization Dev Environment (WSL / Kali Linux)

この環境は、**WSL 上の Kali Linux** に  
**Node.js 20 + npm** を導入し、  
**Vite + React** ベースのブロックチェーン・データ可視化用 Web アプリを  
開発・実行するための構成である。

本環境では、`out/` 配下の CSV 一覧を `index.json` にまとめ、  
フロントエンドが `/out/index.json` を起点として各 CSV を読み込むことで、  
各種データ可視化を行う。

---

## 1. 構成概要

本環境の主な構成要素は次の通りである。

- 実行環境: WSL 上の Kali Linux
- ランタイム: Node.js 20 / npm
- フロントエンド: Vite + React
- 開発サーバ: `localhost:5173`
- データ配置先: `out/`
- マニフェスト生成: `scripts/gen-manifest.cjs`
- 公開用静的パス: `public/out/`

---

## 2. ディレクトリ構成

想定するディレクトリ構成は以下の通りである。

```text
project-root/
├─ package.json
├─ package-lock.json
├─ scripts/
│   └─ gen-manifest.cjs
├─ src/
├─ public/
│   └─ out/
├─ out/
└─ README.md
````

各ディレクトリの役割は次の通りである。

* `src/`
  React / TypeScript のフロントエンドソースを格納する。

* `scripts/gen-manifest.cjs`
  `out/` 配下の CSV 一覧を走査し、`out/index.json` を生成する。

* `out/`
  CSV および `index.json` を配置する作業用ディレクトリである。

* `public/out/`
  ブラウザへ静的配信するための公開ディレクトリである。

---

## 3. 事前準備

### 3.1 WSL 上の Kali Linux を更新する

まず、Kali Linux 側のパッケージ情報を更新する。

```bash
sudo apt update
sudo apt upgrade -y
```

### 3.2 Node.js 20 を導入する

Node.js 20 系を用いることを前提とする。

```bash
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

導入後、以下で確認する。

```bash
node -v
npm -v
```

Node.js 20 系が表示されればよい。

---

## 4. 初回セットアップ

### 4.1 プロジェクトルートへ移動する

```bash
cd ~/your-project-directory
```

### 4.2 必要ディレクトリを作成する

```bash
mkdir -p out
mkdir -p public
mkdir -p scripts
```

### 4.3 依存関係をインストールする

```bash
npm install
```

---

## 5. `gen-manifest.cjs`

`out/` 内の CSV ファイル一覧を `out/index.json` にまとめるスクリプトは以下である。

```js
const fs = require("fs");
const path = require("path");

const outDir = path.resolve(__dirname, "..", "out");
const manifestPath = path.join(outDir, "index.json");

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

const files = fs.readdirSync(outDir).filter(f => f.endsWith(".csv")).sort();

fs.writeFileSync(manifestPath, JSON.stringify({ files }, null, 2));
console.log(`Generated manifest: ${manifestPath} (${files.length} files)`);
```

このスクリプトは、`out/` 配下に存在する `.csv` ファイルのみを抽出し、
ソートした一覧を `index.json` として出力する。

---

## 6. `out/` と `public/out/` の扱い

`public/out/` には、ブラウザから参照させる CSV および `index.json` を配置する。
運用方法としては、次のいずれかを用いる。

### 方法A: `public/out` をシンボリックリンクにする

```bash
rm -rf public/out
ln -s ../out public/out
```

この方法では、`out/` を更新すれば、そのまま `/out/...` として配信される。
通常はこちらを推奨する。

### 方法B: `out/` を `public/out/` に同期する

```bash
mkdir -p public/out
rsync -av --delete out/ public/out/
```

この方法では、公開前に `out/` の内容を `public/out/` へ複製する。
シンボリックリンクを避けたい場合に用いる。

---

## 7. `package.json` の scripts 構成

本環境では、`package.json` の `scripts` を用いて
CSV マニフェスト生成、必要に応じた `public/out/` への同期、
および WSL 向け設定での Vite 開発サーバ起動を行う。

推奨される `package.json` の `scripts` は以下の通りである。

```json
{
  "name": "web-visualization-dev",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "dev:wsl": "vite --host 0.0.0.0 --port 5173",
    "dev:wsl:poll": "CHOKIDAR_USEPOLLING=true WATCHPACK_POLLING=true vite --host 0.0.0.0 --port 5173",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0 --port 4173",
    "gen:manifest": "node scripts/gen-manifest.cjs",
    "sync:out": "mkdir -p public/out && rsync -av --delete out/ public/out/",
    "prepare:data": "npm run gen:manifest",
    "prepare:data:sync": "npm run gen:manifest && npm run sync:out",
    "start": "npm run prepare:data && npm run dev:wsl",
    "start:sync": "npm run prepare:data:sync && npm run dev:wsl",
    "start:poll": "npm run prepare:data && npm run dev:wsl:poll"
  },
  "dependencies": {
  },
  "devDependencies": {
  }
}
```

---

## 8. 各 scripts の役割

### `npm run dev`

標準の Vite 開発サーバを起動するコマンドである。
ホストやポートを明示しない最小構成である。

### `npm run dev:wsl`

WSL 環境から Windows 側ブラウザでアクセスしやすいように、
`0.0.0.0:5173` で Vite を起動するコマンドである。
通常の開発ではこれを基本とする。

### `npm run dev:wsl:poll`

ファイル監視が不安定な場合に使用する。
`CHOKIDAR_USEPOLLING=true` および `WATCHPACK_POLLING=true` を有効にし、
ポーリング方式で変更を検知する。

### `npm run build`

TypeScript のビルドと Vite の本番用ビルドを実行する。

### `npm run preview`

ビルド済み成果物をローカルで確認する。

### `npm run gen:manifest`

`out/` 配下の CSV 一覧を走査し、`out/index.json` を生成する。

### `npm run sync:out`

`out/` の内容を `public/out/` へ同期する。

### `npm run prepare:data`

`gen:manifest` のみを実行する前処理コマンドである。
シンボリックリンク運用時の基本とする。

### `npm run prepare:data:sync`

`gen:manifest` と `sync:out` をまとめて実行する。
同期運用時に使用する。

### `npm run start`

`prepare:data` を実行した後、WSL 向け設定で開発サーバを起動する。
通常利用ではこのコマンドを基本起動方法とする。

### `npm run start:sync`

`prepare:data:sync` を実行した後、WSL 向け設定で開発サーバを起動する。
同期型運用時に使用する。

### `npm run start:poll`

`prepare:data` を実行した後、ポーリング監視付きで開発サーバを起動する。
WSL 上でホットリロードが不安定な場合に使用する。

---

## 9. 起動手順

### 9.1 シンボリックリンク運用の場合

まず `public/out` を `out` にリンクする。

```bash
rm -rf public/out
ln -s ../out public/out
```

その後、以下で起動する。

```bash
npm run start
```

### 9.2 同期運用の場合

```bash
npm run start:sync
```

### 9.3 ポーリング監視付きで起動する場合

```bash
npm run start:poll
```

---

## 10. ブラウザからのアクセス

Windows 側ブラウザで以下へアクセスする。

```text
http://localhost:5173
```

ポートを変更した場合は、そのポート番号へ読み替えること。

---

## 11. Web アプリの動作

起動後、フロントエンドは `/out/index.json` を取得し、
そこに列挙された `/out/*.csv` を読み込んで可視化する。

想定される表示例は次の通りである。

* ブロック提案タイムライン（GitHub 草風）
* ブロック間隔ヒストグラム
* Top Validators
* Priority Queue アルゴリズムシミュレータ

したがって、`out/` に CSV を追加・削除・更新した場合は、
必要に応じて `npm run gen:manifest` を再実行する必要がある。

---

## 12. CSV ファイルの扱い

最低限の要件は以下である。

* 拡張子が `.csv` であること
* `out/` 配下に置かれていること
* 必要に応じて `gen-manifest.cjs` を再実行すること

CSV の厳密な列名や型定義は、各フロントエンド実装に依存する。
したがって、実際に必要なカラム構成は、可視化コンポーネント側の実装に合わせて設計すること。

---

## 13. よく使うコマンド

### 通常起動

```bash
npm run start
```

### 同期運用で起動

```bash
npm run start:sync
```

### ポーリング監視で起動

```bash
npm run start:poll
```

### マニフェストのみ再生成

```bash
npm run gen:manifest
```

### `out/` を `public/out/` に同期

```bash
npm run sync:out
```

### 依存関係を再インストール

```bash
rm -rf node_modules package-lock.json
npm install
```

### 開発サーバを停止

```bash
Ctrl + C
```

---

## 14. トラブルシューティング

### `npm: command not found`

Node.js が導入されていない。
Node.js 20 をインストールすること。

### `EACCES: permission denied`

プロジェクト所有者を修正する。

```bash
sudo chown -R $USER:$USER .
```

### `localhost:5173` にアクセスできない

起動コマンドが `0.0.0.0:5173` で待ち受けているか確認すること。
通常は `npm run start` を用いればよい。

### ポート 5173 が使用中

別ポートで起動するように `scripts` を変更するか、
一時的に以下を実行する。

```bash
npm run dev -- --host 0.0.0.0 --port 5174
```

### CSV を追加したのに反映されない

`index.json` が古い可能性が高い。
以下を再実行する。

```bash
npm run gen:manifest
```

同期運用の場合は続けて以下も実行する。

```bash
npm run sync:out
```

### ホットリロードが安定しない

ポーリング監視付きで起動する。

```bash
npm run start:poll
```

---

## 15. まとめ

この WSL + Kali Linux 構成では、次の開発環境を構築できる。

* Node.js 20 ベースの Vite + React 開発環境
* `out/` 配下の CSV を `index.json` にまとめる仕組み
* `/out/index.json` を起点とした CSV 可視化
* `localhost:5173` でのローカル開発
* 必要に応じたポーリング監視と同期運用

本環境では、Node.js 20 で依存関係を導入し、
`gen-manifest.cjs` を実行し、
Vite サーバを起動する流れを基本とする。
したがって、`package.json` の `scripts` と通常のシェル操作を用いれば、
WSL 上で一貫した開発運用が可能である。
