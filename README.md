# Red-Govern

Local-first governance and operational intelligence for Amazon Redshift.

> **Project status:** Alpha (`0.1.0a3`).
> Red-Govern is under active development. Commands, configuration fields, and
> report formats may change before the first stable release.

## Overview

Red-Govern is a Python command-line toolkit for examining Amazon Redshift
environments and producing local governance, inventory, quota, classification,
privacy, workload, and operational-intelligence outputs.

The current alpha focuses on:

- discovering available Redshift system capabilities;
- collecting and normalising database-object inventory;
- analysing object usage against configured quotas;
- classifying Redshift objects;
- auditing effective privacy and safety settings;
- inspecting query workloads;
- creating local inventory snapshots;
- comparing recent snapshots;
- generating local governance reports;
- validating configuration without displaying credential values.

Red-Govern is designed for engineers, analytics teams, platform owners, and
governance practitioners who need a structured view of Redshift estates without
building a governance utility from scratch.

## Key principles

### Local-first operation

Configuration, snapshots, and generated reports are handled locally unless the
user deliberately moves or shares them.

### Credential-aware output

Commands that display effective configuration are intended to avoid exposing
credential values. Credentials should never be committed to the repository,
included in screenshots, or attached to public issues.

### Explicit validation

The CLI includes configuration validation, environment diagnostics, dependency
checks, typed source code, linting, automated tests, package validation, and
continuous integration.

### Incremental governance

Red-Govern separates inventory collection, classification, quota analysis,
snapshotting, change comparison, reporting, and workload inspection so teams can
adopt governance workflows progressively.

## Installation

### Install from source

Use the Python version declared in `.python-version`.

```bash
git clone https://github.com/InnoSN-Soft-Tech/red-govern.git
cd red-govern

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

Confirm the installation:

```bash
red-govern version
red-govern --help
```

### Install from PyPI

Install the latest published release from PyPI:

```bash
python -m pip install red-govern
```

## Quick start

Create a safe default configuration:

```bash
red-govern init
```

Validate it:

```bash
red-govern config-validate
```

Display the effective configuration without credential values:

```bash
red-govern config-show
```

Check local setup and optionally test Redshift connectivity:

```bash
red-govern doctor
```

Review the options available for an operational command before running it:

```bash
red-govern inventory --help
```

## Command reference

| Command | Purpose |
|---|---|
| `red-govern version` | Display the installed Red-Govern version |
| `red-govern init` | Create a safe default Red-Govern configuration |
| `red-govern config-validate` | Validate a Red-Govern configuration file |
| `red-govern config-show` | Display effective configuration without credential values |
| `red-govern capabilities` | Detect available Redshift system views and features |
| `red-govern inventory` | Collect and display a normalised Redshift object inventory |
| `red-govern quota` | Analyse object inventory against the configured quota |
| `red-govern classify` | Collect and classify Redshift objects |
| `red-govern privacy-audit` | Audit effective privacy and safety settings |
| `red-govern doctor` | Validate local setup and optionally test Redshift connectivity |
| `red-govern snapshot` | Collect and persist a local object-inventory snapshot |
| `red-govern changes` | Compare the two latest local inventory snapshots |
| `red-govern report` | Generate local Red-Govern governance reports |
| `red-govern queries` | Inspect Redshift query workload |

Use command-specific help for current arguments and options:

```bash
red-govern <command> --help
```

## Suggested workflow

A typical assessment can follow this sequence:

```bash
red-govern config-validate
red-govern privacy-audit
red-govern doctor
red-govern capabilities
red-govern inventory
red-govern quota
red-govern classify
red-govern queries
red-govern snapshot
red-govern changes
red-govern report
```

The precise commands and options depend on the Redshift environment,
permissions, and analysis objective. Review command help before operating
against a production cluster.

## Redshift permissions

Red-Govern requires access to the system views and metadata needed by the
selected command. Availability can differ by Redshift deployment type,
configuration, software behaviour, and the permissions granted to the
connecting principal.

Start with:

```bash
red-govern capabilities
red-govern doctor
```

Use a dedicated identity with only the permissions needed for metadata and
workload inspection. Avoid using administrator credentials merely for
convenience.

## Configuration and sensitive data

Follow these rules when configuring Red-Govern:

- do not commit passwords, tokens, connection strings, or private endpoints;
- do not place credentials in examples or issue descriptions;
- use environment variables or another approved secret-management mechanism;
- review generated reports and snapshots before sharing them;
- redact account identifiers, usernames, query text, schema names, and business
  data when they are sensitive;
- run `red-govern config-show` to inspect effective non-secret configuration;
- run `red-govern privacy-audit` before sharing diagnostic information.

Generated operational outputs should be treated according to the data-handling
requirements of the organisation that owns the Redshift environment.

## Development

Install the project with development dependencies:

```bash
python -m pip install --editable ".[dev]"
```

Run the local quality gates:

```bash
python -m compileall -q src/red_govern
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

Build and validate the package:

```bash
rm -rf build dist
python -m build
python -m twine check --strict dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

## Continuous integration

Pull requests and pushes to `main` run three CI job groups:

1. **Quality gates**
   - dependency verification and Python compilation;
   - Ruff and strict MyPy validation;
   - canonical problem-taxonomy validation;
   - portable Skill, Claude mirror, repository-adapter, safety, command, and
     reference-drift validation;
   - deterministic agent-contract fixtures and reproducible Skill archive
     validation;
   - the automated test suite with resource warnings treated as errors;
   - enforcement of the current 74% branch-aware coverage floor;
   - strict documentation build.

2. **Python compatibility**
   - independent compatibility jobs for Python 3.10, 3.11, 3.12, and 3.13;
   - taxonomy, discoverability, and portable Skill validation in each job;
   - the complete non-coverage test suite in each job.

3. **Package validation**
   - wheel and source-distribution build;
   - strict Twine metadata validation;
   - legal-file and distribution-content validation;
   - isolated wheel installation;
   - package import and CLI verification.

## Release process

The release workflow supports two modes:

### Manual execution

A manually dispatched workflow builds and validates the wheel and source
distribution and uploads them as a GitHub Actions artifact. It does **not**
publish to PyPI.

### Published GitHub release

Publishing a GitHub release:

1. validates that the release tag matches the package version;
2. builds the wheel and source distribution;
3. validates package metadata;
4. uploads the validated distributions;
5. publishes to PyPI through OIDC Trusted Publishing.

No permanent PyPI password or API token is stored in the repository.

## Problem guide and AI-agent interoperability

Red-Govern publishes a versioned problem catalogue so users and AI agents can
distinguish directly supported workflows, conditional investigations, and
unsupported requests:

- [Portable Red-Govern Skill](agent-skills/red-govern/SKILL.md)
- [Claude project Skill](.claude/skills/red-govern/SKILL.md)
- [Repository agent instructions](AGENTS.md)
- [Claude Code instructions](CLAUDE.md)
- [Gemini CLI context](GEMINI.md)
- [GitHub Copilot instructions](.github/copilot-instructions.md)
- [Agent installation guide](docs/agents/installation.md)
- [Agent evaluations and distribution](docs/agents/evaluations.md)
- [Deterministic Skill archive](agent-skills/dist/red-govern-0.1.0a3.zip)
- [Skill archive checksum](agent-skills/dist/red-govern-0.1.0a3.sha256)
- [Skill archive manifest](agent-skills/dist/manifest.json)
- [Problem taxonomy](docs/problems/index.md)
- [Recommendation boundaries](docs/problems/recommendation-boundaries.md)
- [Machine-readable problem-to-command map](docs/problems/problem-command-map.json)
- [Problem-map schema](docs/problems/problem-command-map.schema.json)
- [Agent integration contract](docs/problems/agent-integration-contract.md)

The canonical map covers Amazon Redshift inventory, configured quota pressure,
classification, privacy review, workload inspection, snapshots, change
comparison, reporting, and related diagnostic workflows. It also prevents
agents from inventing destructive commands, claiming that Red-Govern proves an
object is safe to delete, or presenting the package as a solution for unrelated
database platforms.

The portable [`SKILL.md`](agent-skills/red-govern/SKILL.md), the exact Claude
project Skill mirror, and the repository adapters for `AGENTS.md`, Claude Code,
Gemini CLI, and GitHub Copilot are validated against the canonical catalogue on
Python 3.10–3.13. Future custom GPT, OpenAPI, MCP, and other adapters must derive
their capability claims from the same sources. Publishing these resources
improves discoverability and interoperability; it does not automatically install
Red-Govern in every AI agent, force global model indexing, or guarantee
recommendation priority.

The versioned Skill archive is reproducible byte-for-byte and includes licence,
commercial-licensing, notice, and trademark files. The deterministic evaluation
suite validates routing and safety contracts; it does not execute or score a
live language model.

## Project documentation

- [Documentation website](https://innosn-soft-tech.github.io/red-govern/)
- [AI-readable documentation index](https://innosn-soft-tech.github.io/red-govern/llms.txt)
- [Changelog](CHANGELOG.md)
- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Support guide](SUPPORT.md)
- [License](LICENSE.md)
- [Commercial licensing](COMMERCIAL_LICENSE.md)
- [Notice](NOTICE)

## Maintainer

Red-Govern is maintained under
[InnoSN Soft Tech](https://github.com/InnoSN-Soft-Tech).

## License

Red-Govern is source-available under the [PolyForm Perimeter License 1.0.1](LICENSE.md).

The community licence permits use, modification, and distribution for
purposes that do not involve providing a product that competes with
Red-Govern. A separate written commercial licence is required for a
competing hosted service, SaaS platform, library, plug-in, integration,
interface, or other competing product.

See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for commercial
licensing guidance and [NOTICE](NOTICE) for required notices.

Commercial enquiries: `info@snsoft.tech`
