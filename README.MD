# 🐬 Diver V0.1
Enhances your development workflow but also aligns with the principles of open-source and local-first computing, with a complete local inferance through CLI.

### Overview

Diver is a lightweight local-first developer CLI that helps you search, edit, run and inspect code in a project. It includes a small local LLM bridge (Ollama), a vector-based code search index, and a convenient interactive shell.

## Quick start

1. Install required OS packages on WSL (example):

```bash
sudo apt update
sudo apt install build-essential g++ gcc nodejs npm python3
# For Rust (optional):
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

2. Create and activate the conda environment (recommended):

```bash
# Create the environment from env.yml (runs on conda/mamba)
conda env create -f env.yml
conda activate diver
```

3. (Optional) Install the package in editable mode so you can run the `diver` console script:

```bash
# from the repository root
pip install -e .
# now you can run just:
diver
# or run directly without installing:
python3 diver.py
```

## Diver CLI commands

When started you get a prompt. Commands begin with a colon `:`.

Note: the `:` prefix is how you invoke Diver's commands inside the interactive CLI (this works the same on Linux/WSL). To run shell commands from the Diver prompt, prefix them with `:` as well (for example `:ls`, `:pwd`, `:git status`) — unknown `:<command>` strings are forwarded to your shell.

- `:index` — Index the codebase (reads files from `config.CODE_DIR`, creates embeddings and populates the local vector DB).
- `:search <query> [--ext .py]` — Search the codebase. Optionally append `--ext` or a language token (e.g. `rs`, `py`) to restrict results to files with that extension.
- `:run <file>` — Compile or run a file. Supports:
	- Python (`.py`) — runs with `DEFAULTS['python']` (falls back to `python`)
	- JavaScript (`.js`) — runs with `DEFAULTS['node']`
	- TypeScript (`.ts`) — uses `npx ts-node`, `ts-node`, or compiles via `tsc` then `node`
	- Rust (`.rs`) — compiles with `DEFAULTS['rustc']`
	- C (`.c`) — compiles with `DEFAULTS['gcc']` or `DEFAULTS['clang']`
	- C++ (`.cpp`, `.cc`) — compiles with `DEFAULTS['gpp']` or `DEFAULTS['clangpp']`

	Compiled binaries are placed into `DEFAULTS['build_dir']` (default `build`) and executed from there to avoid name collisions.

- `:edit <file>` — Open a file in your $EDITOR (default `vim`) and write changes back when you exit.
- `:cd <dir>` — Change the CLI working directory (affects `:run`, shell commands, and file paths).
- `:quit` / `:exit` — Exit the CLI.

Any unknown `:<command>` is forwarded to your shell, so you can run `:ls`, `:pwd`, `:git status`, etc.


## Configuration

Settings are centralized in `config.py` under the `DEFAULTS` dict. Example keys you can change:

- `python` — which python executable to use (default `python2`)
- `node` — which node executable to use (default `node`)
- `ts_node`, `npx`, `tsc` — TypeScript toolchain
- `gcc`, `gpp`, `clang`, `clangpp` — C/C++ compilers
- `rustc` — Rust compiler
- `build_dir` — directory where compiled binaries are written (default `build`)
- `editor` — default editor (used if $EDITOR is not set)

Edit `config.py` to override these defaults. You can also set your shell `$EDITOR` environment variable before launching the CLI (e.g., `export EDITOR="code --wait"`).


## Notes & Troubleshooting

- If a `:run` result seems to run the wrong program (e.g., you see `Process exited with code 1` when running `:run test`), it is most likely a system command conflict. Diver compiles binaries into `build/` and executes them from there to avoid the `test` binary conflict. If you still see problems, check `DEFAULTS['build_dir']` and the printed compile/run commands.
- If search returns irrelevant files, run `:index` again to refresh the vector DB. Use `:search <query> --ext rs` to restrict to Rust sources.
- LLM features require Ollama (or a compatible local LLM) to be installed and running; ensure `ollama` is available if you use `ask_model` features.

## Development notes

- `cli.py` — main interactive shell and command implementations.
- `search.py` — vector search logic (uses embedder and Chroma client).
- `indexer.py` — walks files and chunks text for indexing.
- `model.py` — small wrapper around Ollama subprocess for LLM queries.
- `config.py` — global settings (DEFAULTS) and lazy resource getters.

## Future updates:
V0.2 - Possiblity to commit changes in the source code through the editor, interactively, by acceting sections and what not.
V0.3 - ...
