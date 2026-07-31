# Changelog

All notable changes to Red-Govern are documented in this file.

The project follows the principles of
[Semantic Versioning](https://semver.org/). Because the project is currently in
alpha, functionality and interfaces may change between releases.

## Unreleased

No unreleased changes have been recorded yet.

## 0.1.0a1 - 2026-07-30

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
