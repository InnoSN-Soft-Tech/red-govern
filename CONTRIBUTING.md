# Contributing to Red-Govern

Thank you for considering a contribution to Red-Govern.

The project is currently in alpha. Small, focused, well-tested contributions are
preferred over large changes that combine unrelated behaviour.

Because Red-Govern uses a source-available and dual-licensing model,
source-code contributions require prior written approval and applicable
contributor terms from InnoSN Soft Tech (OPC) Private Limited. Bug
reports, feature proposals, and documentation suggestions remain welcome.

## Ways to contribute

Contributions may include:

- bug reports;
- reproducible Redshift compatibility findings;
- documentation improvements;
- test coverage;
- query and metadata compatibility improvements;
- classification or governance-rule improvements;
- privacy and safety improvements;
- performance improvements;
- focused feature proposals.

For general usage questions, follow [SUPPORT.md](SUPPORT.md). For
security-sensitive reports, follow [SECURITY.md](SECURITY.md).

## Development setup

Fork or clone the repository and create a virtual environment:

```bash
git clone https://github.com/InnoSN-Soft-Tech/red-govern.git
cd red-govern

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

Use the Python version declared in `.python-version`.

## Branches

Create a focused branch from the latest `main`:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/short-description
```

Common branch prefixes include:

- `feature/`
- `fix/`
- `docs/`
- `test/`
- `refactor/`
- `chore/`
- `ci/`

Do not commit directly to `main`.

## Code quality

Before committing, run:

```bash
python -m compileall -q src/red_govern
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

For packaging changes, also run:

```bash
rm -rf build dist
python -m build
python -m twine check --strict dist/*
```

New behaviour should include tests where practical. Existing tests should not be
removed merely to make a change pass.

## Coding expectations

Contributions should:

- preserve type safety;
- use clear and descriptive names;
- keep functions and modules focused;
- provide actionable error messages;
- avoid logging credentials or sensitive values;
- avoid unnecessary network activity;
- preserve local-first behaviour;
- handle unavailable Redshift capabilities explicitly;
- avoid assuming that every Redshift system view is available;
- include comments only where they add useful context.

## Redshift-sensitive contributions

When contributing examples, fixtures, logs, or screenshots:

- do not include live credentials;
- redact account IDs, cluster identifiers, endpoints, users, and database names;
- remove proprietary schema, table, column, and query information;
- use synthetic data wherever possible;
- state whether behaviour was tested against provisioned Redshift, Redshift
  Serverless, or a mocked environment;
- describe the minimum permissions used for the test.

## Commit messages

Use concise, imperative commit messages. Conventional-style prefixes are
encouraged:

```text
feat: add inventory filter
fix: handle unavailable system view
docs: clarify configuration setup
test: cover quota edge case
ci: validate release distributions
chore: update development dependency
```

## Pull requests

A pull request should contain:

- a clear problem statement;
- a concise summary of the implementation;
- testing performed;
- relevant compatibility notes;
- security or privacy implications;
- screenshots or sample output only when properly redacted.

Keep pull requests limited to one coherent change.

## Pull-request checklist

Before requesting review, confirm that:

- [ ] the branch is based on the latest `main`;
- [ ] the working tree contains only intended changes;
- [ ] compilation succeeds;
- [ ] Ruff passes;
- [ ] MyPy passes;
- [ ] tests pass;
- [ ] package validation passes when packaging is affected;
- [ ] documentation is updated where required;
- [ ] no credentials or sensitive operational data are included;
- [ ] generated build files are not committed.

## Contribution licensing

Red-Govern uses a source-available and dual-licensing model. Do not submit
source-code contributions unless InnoSN Soft Tech (OPC) Private Limited
has approved the contribution and applicable contributor terms in writing.

Submitting a pull request does not by itself grant InnoSN Soft Tech the
right to relicense, commercially license, or incorporate the contribution.
An approved contributor agreement or other written arrangement may be
required before a source-code contribution can be accepted.

Bug reports, feature proposals, compatibility findings, and documentation
suggestions may be submitted without transferring ownership of unrelated
materials.

Licensing questions: `info@snsoft.tech`
