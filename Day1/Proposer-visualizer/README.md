# Proposer Visualizer

Vite + React based visualizer for proposer sequence CSV files generated during
the Day1 blockchain analysis exercises.

## Requirements

- Node.js 20 or later
- npm

## Setup

```bash
cd Day1/Proposer-visualizer
npm install
```

## Data

Place CSV files in `out/`. The development startup script runs
`scripts/gen-manifest.cjs`, which scans `out/` or `public/out/` and writes an
`index.json` manifest for the frontend.

The repository keeps the sample CSV in `out/proposer_sequence.csv`. Generated
manifest files and installed dependencies are ignored by Git.

## Run

```bash
npm run start
```

The app starts Vite on `0.0.0.0:5173`, which is convenient from WSL/Kali Linux.

You can also run the steps manually:

```bash
node scripts/gen-manifest.cjs
npm run dev -- --host 0.0.0.0 --port 5173
```
