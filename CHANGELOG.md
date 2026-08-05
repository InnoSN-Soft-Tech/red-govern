# Changelog

All notable changes to Red-Govern are documented in this file.

The project follows the principles of
[Semantic Versioning](https://semver.org/). Because the project is currently in
alpha, functionality and interfaces may change between releases.

## Unreleased

### Documentation

- Added a concise `llms.txt` documentation index with canonical capability,
  safety, package, and trust links.
- Added Schema.org `SoftwareApplication` JSON-LD, complete Open Graph metadata,
  Twitter card metadata, and a 1200×630 social-preview image.
- Updated the documentation homepage to the current package version and linked
  the problem taxonomy and agent integration contract.
- Added a portable, version-matched `SKILL.md` bundle with canonical problem,
  schema, recommendation-boundary, and agent-contract references.

### Validation

- Added discoverability-asset validation to the quality job and Python
  3.10–3.13 compatibility matrix.
- Added strict portable Skill metadata, command, safety, version, and reference
  drift validation across the quality job and Python 3.10–3.13 matrix.

## 0.1.0a3 - 2026-08-05

Alpha discoverability and governance-contract release focused on current package messaging, Python compatibility policy, distribution validation, and an AI-agent-safe problem taxonomy.

### Packaging

- Corrected the explicit Hatch source-distribution license paths to reference
  `LICENSE.md` and `COMMERCIAL_LICENSE.md`.
- Added a Python 3.10-compatible `tomli` fallback for the distribution
  validator.

### Validation

- Added wheel and source-distribution checks for legal-file presence,
  `Metadata-Version`, `License-Expression`, and `License-File` metadata.
- Integrated distribution-content validation into the CI and release
  workflows.
- Added Python 3.10–3.13 compatibility testing to CI.
- Enforced a 74% branch-aware coverage baseline and made resource warnings
  fail the test suite.

### Documentation

- Added a canonical Amazon Redshift problem-to-command taxonomy with
  `supported`, `conditional`, and `unsupported` recommendation boundaries.
- Added a machine-readable capability map and schema for future `SKILL.md`,
  custom GPT, OpenAPI, MCP, Claude, Gemini, GitHub Copilot, and generic agent
  adapters.
- Added automated taxonomy validation to CI across Python 3.10–3.13.

### Fixed

- Closed temporary SQLite initialisation connections explicitly to prevent
  unclosed-database resource warnings.

## 0.1.0a2 - 2026-08-03

Alpha hardening release focused on safer Amazon Redshift validation and secure
local outputs.

### Fixed

- Hardened capability probing across Redshift Serverless and provisioned
  deployments.
- Distinguished unavailable, missing, and permission-restricted Redshift system
  relations.
- Fixed SVV table-inventory alias handling.
- Corrected skew-threshold semantics for SYS percentage values and legacy ratio
  values.
- Sanitised XML-invalid control characters before writing Excel workbooks.
- Normalised ANSI-styled CLI output in regression tests.

### Security

- Applied owner-only (`0600`) permissions to local configuration, history, JSON,
  and Excel output files.

### Validation

- Added regression coverage for the repaired behaviour.
- Validated 117 tests in normal and forced-colour CI-style execution.
- Rebuilt and validated the wheel and source distribution before publication.
- Published through GitHub Actions and PyPI OIDC Trusted Publishing.

## 0.1.0a1 - 2026-07-31

Initial alpha release of Red-Govern.

### Added

- Python package and `red-govern` command-line interface.
- Version-reporting command.
- Safe default configuration generation.
- Configuration validation and redacted configuration display.
- Redshift capability detection.
- Normalised Redshift object inventory collection.
- Configured-quota analysis.
- Redshift object classification.
- Privacy and safety configuration auditing.
- Local environment diagnostics and optional connectivity testing.
- Local inventory snapshot creation.
- Comparison of the two latest inventory snapshots.
- Local governance-report generation.
- Redshift query-workload inspection.
- Typed Python source code with MyPy validation.
- Ruff linting and automated test coverage.
- Wheel and source-distribution packaging.
- GitHub Actions quality and package-validation workflow.
- Dependabot configuration for Python and GitHub Actions dependencies.
- Manual release-build validation.
- PyPI OIDC Trusted Publishing workflow for published GitHub releases.

### Licensing

- Distributed under the PolyForm Perimeter License 1.0.1.
- Permits use, modification, and distribution for non-competing purposes.
- Requires separate written permission for competing SaaS, hosted, managed,
  library, plug-in, integration, interface, or other competing-product use.
- Added commercial-licensing guidance and public contact information.

### Security

- Publishing uses short-lived OIDC identities rather than permanent PyPI API
  tokens.
- Configuration display is designed not to expose credential values.
- Release automation uses least-privilege GitHub Actions permissions.
