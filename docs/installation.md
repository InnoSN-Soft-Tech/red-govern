# Installation

Red-Govern requires Python 3.10 or later. Use an isolated virtual environment so
the package and its dependencies do not interfere with other Python projects.

## Install from PyPI

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the latest published release:

```bash
python -m pip install red-govern
```

Confirm the installation:

```bash
red-govern version
red-govern --help
```

## Install from source

Clone the public repository and install the project in editable mode:

```bash
git clone https://github.com/InnoSN-Soft-Tech/red-govern.git
cd red-govern

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

Run the local validation gates:

```bash
python -m compileall -q src/red_govern
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

## Preview the documentation

Documentation dependencies are intentionally kept separate from package runtime
dependencies:

```bash
python -m pip install --requirement requirements-docs.txt
mkdocs serve
```

Open the local address printed by MkDocs. Build the static site with strict
warning handling before publishing:

```bash
mkdocs build --strict
```

Continue with the [quick start](quick-start.md) after the CLI is installed.
