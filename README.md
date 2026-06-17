# sus_BC2

Blockchain and crypto-asset security exercises for the BC2 experiment series.
The repository is organized by experiment day and includes Python simulations,
Injective/SimBlock setup notes, and a React-based proposer visualizer.

## Repository Layout

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
requirements.txt
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The experiment notes assume WSL with Kali Linux for tools such as
`injectived`, SimBlock, Java, Node.js, and npm. The longer environment setup
memo is kept in [docs/injective-setup.md](docs/injective-setup.md).

## Python Experiments

Run each script from the repository root unless a script-specific note says
otherwise.

```bash
python Day1/1-1_block-fetch.py
python Day2/2-1mm1_queue.py
python Day3/3-1_btc_mining.py
```

## Proposer Visualizer

```bash
cd Day1/Proposer-visualizer
npm install
npm run start
```

The visualizer reads CSV files from `out/` and generates `out/index.json`
before starting Vite on port 5173. Dependencies such as `node_modules/` are
intentionally excluded from Git.

## Additional Notes

- `command.md` and `2-4command.md` keep command history and experiment-specific
  run notes.
- `jikken_txt.pdf` is retained as the original experiment reference document.
- `command.env.example` is a placeholder for local environment values. Do not
  commit real wallet keys, mnemonics, or private RPC credentials.
