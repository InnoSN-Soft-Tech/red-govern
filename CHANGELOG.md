# Changelog

All notable changes to Red-Govern are documented in this file.

The project follows the principles of
[Semantic Versioning](https://semver.org/). Because the project is currently in
alpha, functionality and interfaces may change between releases.

## Unreleased

### API

- Implemented the optional FastAPI remote metadata runtime for the four frozen GET operations without Redshift connectivity, SQL or command execution, credential intake, or local-configuration upload.
- Defined a contract-only read-only remote metadata API with four GET operations and an OpenAPI 3.1 schema; no server, Redshift connection, SQL execution, or Custom GPT Action was enabled.
- Added an optional OpenAI Agents SDK adapter exposing the four offline-safe typed API operations as strict function tools without model execution.
- Added an optional local stdio MCP adapter exposing four structured, offline-safe configuration and privacy tools over the typed Python API.
- Kept MCP outside the base dependency set and limited the first adapter to local stdio with no Redshift connection, SQL execution, file-writing tool, hosted transport, or OpenAI API key.
- Added a typed, presentation-independent Python API for version inspection,
  configuration validation, redacted effective configuration, and structured
  privacy auditing.
- Kept the first API contract offline-safe: no Redshift connection, file
  writes, MCP dependency, model execution, or OpenAI API key is required.

### Documentation

- Added the remote metadata API contract, OpenAPI schema, planned server boundary, and a populated privacy notice for future public Action readiness.
- Added OpenAI Agents SDK adapter construction, isolated-installation, tool, and safety-boundary documentation.
- Added local stdio MCP installation, client-configuration, tool, and safety-boundary documentation.
- Added a concise `llms.txt` documentation index with canonical capability,
  safety, package, and trust links.
- Added Schema.org `SoftwareApplication` JSON-LD, complete Open Graph metadata,
  Twitter card metadata, and a 1200×630 social-preview image.
- Updated the documentation homepage to the current package version and linked
  the problem taxonomy and agent integration contract.
- Added a portable, version-matched `SKILL.md` bundle with canonical problem,
  schema, recommendation-boundary, and agent-contract references.
- Added repository instructions for `AGENTS.md`, Claude Code, Gemini CLI, and
  GitHub Copilot, plus an exact project-local Claude Skill mirror.
- Added agent installation, evaluation, deterministic distribution, licence,
  notice, commercial-licensing, and trademark documentation.
- Added a downloadable versioned Skill archive with checksum and manifests.
- Added a version-controlled Custom GPT asset bundle with private-first
  configuration, explicit instructions, six conversation starters, and a
  10-file knowledge manifest aligned with the OpenAI limit checked on
  2026-08-06.
- Added a 36-case Custom GPT acceptance plan and publishing checklist;
  Actions and runtime integrations remain deferred to Step 47.

### Validation

- Added remote-runtime route, payload, packaged-map parity, network-isolation, dependency-boundary, and isolated CI tests.
- Added deterministic remote metadata contract tests and CI validation across the quality and Python 3.10–3.13 job groups.
- Added isolated OpenAI Agents SDK CI and 11 adapter contract tests while preserving the MCP 2.x validation environment.
- Added in-memory MCP protocol tests and deterministic validation for the exact tool set, structured outputs, sanitized errors, stdio-only transport, and dependency boundary.
- Added discoverability-asset validation to the quality job and Python
  3.10–3.13 compatibility matrix.
- Added strict portable Skill metadata, command, safety, version, and reference
  drift validation across the quality job and Python 3.10–3.13 matrix.
- Extended agent-asset validation to enforce the Claude Skill mirror, thin
  non-conflicting platform adapters, and repository-instruction safety rules.
- Added 28 deterministic contract fixtures and cross-version evaluation.
- Added byte-for-byte deterministic Skill archive validation on Python
  3.10–3.13.
- Added Custom GPT asset validation to the quality job and Python
  3.10–3.13 compatibility matrix.
- Hardened Custom GPT Preview contracts for the exact command allowlist,
  pinned alpha installation, version-mismatch handling, and uploaded-source
  citation after the initial 5/8 manual Preview round.
- Synchronized editor-safe Custom GPT instructions at 5,195 characters,
  enforced the 8,000-character editor limit and exact instruction digest,
  and recorded the successful 8/8 manual Preview acceptance.

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
