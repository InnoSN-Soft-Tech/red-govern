# Changelog

All notable changes to Red-Govern are documented in this file.

The project follows the principles of
[Semantic Versioning](https://semver.org/). Because the project is currently in
alpha, functionality and interfaces may change between releases.

## Unreleased

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
