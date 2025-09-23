<div align="center">

# uv-burn

Convert `uv` (Astral's ultra-fast Python package manager) project metadata (`pyproject.toml` + `uv.lock`) into **Pipenv** (`Pipfile` + `Pipfile.lock`) so tools (notably **Veracode**) that do **not yet support `uv` projects** can successfully perform dependency / SCA & static scans.

</div>

<!-- Badges (add once available on PyPI / CI) -->
<!--80
![PyPI Version](https://img.shields.io/pypi/v/uv-burn)
![License](https://img.shields.io/github/license/brainslush/uv-burn)
![Python Versions](https://img.shields.io/pypi/pyversions/uv-burn)
-->

## Table of Contents
- [Why does this exist?](#why-does-this-exist-the-veracode-gap-️)
- [Features](#features-)
- [Installation](#installation-)
- [Quick start](#quick-start-)
- [CLI options](#cli-options)
- [Authenticated indices](#authenticated-indices)
- [How it works](#how-it-works-)
- [Limitations](#limitations-️)
- [Contributing](#contributing-)
- [FAQ](#faq-)
- [Inspiration & Acknowledgements](#inspiration--acknowledgements-)
- [License](#license-)

## Why does this exist? (The Veracode gap)
As of 2025, Veracode's Python ecosystem detection supports projects that use **Poetry** or **Pipenv** (and classic `requirements.txt` flows in some pipelines). The emerging `uv` workflow produces a `uv.lock` file which Veracode currently ignores, resulting in scans that:

- Fail to identify transitive dependencies
- Report missing package manager / manifest warnings
- Potentially under-report vulnerable packages

`uv-burn` acts as a compatibility bridge: it synthesizes a `Pipfile` + fully hashed `Pipfile.lock` from your existing `pyproject.toml` & `uv.lock`, preserving:

- Sources / custom indices (including auth via environment variables)
- Resolved versions and hashes
- Python version requirements
- Markers (incl. per‑package python_version constraints fetched from indexes when needed)

No re-resolution is attempted: the tool faithfully projects the lock state into the Pipenv schema.

> NOTE: This project is not affiliated with Astral, Pipenv, or Veracode. It's a pragmatic helper until native `uv` support lands in security tooling.

## Features
- Multi-`pyproject.toml` discovery (monorepos)
- Converts `uv.lock` + all discovered project dependency declarations into:
	- `Pipfile`
	- `Pipfile.lock` (hashes, markers, indices)
- Preserves custom package indices (adds default PyPI if missing)
- Fetches per-package `requires-python` markers from indices to build accurate Pipenv markers
- Deterministic hashing (matches Pipenv's lock hash approach for meta section)
- Async index fetch for performance
- Safe by default: refuses to overwrite unless `--force`

## Installation
Install from source (until published on PyPI):

```bash
pip install uv-burn

# From a local clone
pip install -e .
```

## Quick start
Inside a repository that already contains at least one `pyproject.toml` and a `uv.lock`:

```bash
uv-burn .
```

Outputs (by default in the provided root path):
- `Pipfile`
- `Pipfile.lock`

### CLI options
```text
uv-burn [ROOT_PATH] [--output PATH] [--force] [--verbose]
```

| Option | Description |
| ------ | ----------- |
| `ROOT_PATH` | Root directory to scan (recursive) for `pyproject.toml` + `uv.lock`. |
| `-o, --output` | Directory to write `Pipfile` + `Pipfile.lock` (defaults to root). |
| `-f, --force` | Overwrite existing Pipfile artifacts if present. |
| `-v, --verbose` | Enable debug logging (rich formatted). |

### Example (monorepo)
```bash
uv-burn ./services/ --output ./pipenv-export/
```

### Authenticated indices
Environment variables are auto-detected per index name:

```
UV_INDEX_<INDEXNAME>_USERNAME
UV_INDEX_<INDEXNAME>_PASSWORD
```

Example for an index declared as `name = "internal"`:
```bash
export UV_INDEX_INTERNAL_USERNAME=myuser
export UV_INDEX_INTERNAL_PASSWORD=secret
uv-burn .
```

## How it works
1. Recursively finds all `pyproject.toml` files
2. Loads `uv.lock`
3. Builds a combined source list (default PyPI + declared `tool.uv.indices`)
4. Parses project dependencies (markers, extras, direct URLs / git)
5. Computes `Pipfile` meta hash
6. For each external package in the lock:
	 - Gathers wheel / sdist hashes
	 - Enriches with `requires-python` (queried from the index JSON Simple API)
	 - Builds Pipenv marker string
7. Writes `Pipfile` + JSON `Pipfile.lock`

## Limitations
- Not meant for project conversion; keep using `uv` for development
- Development dependencies currently not exported (section left empty)
- Does not re-resolve dependencies; assumes `uv.lock` is authoritative
- Only first discovered project's `requires-python` used for Pipfile `requires` (multi-root nuance)
- Git / direct URL dependencies: basic handling; lock fidelity may vary if Pipenv's semantics differ
- Does not attempt environment marker normalization beyond Python version & those present in `uv.lock`

## Contributing
Pull requests welcome! Suggested flow:
1. Fork & create a feature branch
2. Maintain style (ruff rules configured)
3. Add / adapt tests (to be added as project matures)
4. Open PR explaining motivation / behaviour change

### Dev environment
```bash
uv sync
```

Run lint:
```bash
ruff check .
```

Run formatting:
```bash
ruff format .
```

## FAQ
**Q: Why not have Veracode just support `uv`?**  
We're waiting. This tool fills the interim gap.

**Q: Is the produced Pipfile intended for ongoing dev use?**  
Primarily for scanning artifacts; you should keep `uv` as your development workflow.

**Q: Are hashes trustworthy?**  
Hashes are taken from `uv.lock` entries (wheels / sdist) without modification.

**Q: What about license compliance scans?**  
Those should work once dependencies are discoverable via the synthesized `Pipfile.lock`.

## Inspiration & Acknowledgements
- Astral for `uv`

## License
MIT – see `LICENSE` file.
