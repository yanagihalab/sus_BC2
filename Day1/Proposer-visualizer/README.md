# Proposer Visualizer

Day1 のブロック解析で生成した proposer sequence CSV を可視化する Vite + React アプリである。

## 必要なもの

- Node.js 20 以降
- npm

## セットアップ

```bash
cd Day1/Proposer-visualizer
npm install
```

## データ配置

CSV ファイルは `out/` に配置する。
起動時に `scripts/gen-manifest.cjs` が `out/` または `public/out/` を走査し、フロントエンドが読み込む `index.json` を生成する。

このリポジトリにはサンプルとして `out/proposer_sequence.csv` を含めている。
生成される manifest、build 出力、`node_modules/` は Git 管理対象外である。

## 起動

```bash
npm run start
```

`npm run start` は manifest を生成した後、Vite を `0.0.0.0:5173` で起動する。
WSL / Kali Linux から Windows 側ブラウザで確認する場合にも使いやすい設定である。

手動で実行する場合は、次の順に実行する。

```bash
node scripts/gen-manifest.cjs
npm run dev -- --host 0.0.0.0 --port 5173
```
