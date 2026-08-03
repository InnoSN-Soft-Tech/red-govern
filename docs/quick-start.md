# Quick start

This workflow creates a safe starter configuration, validates it, and inspects
the environment before running operational commands.

## 1. Create the configuration

```bash
red-govern init
```

The generated configuration is a starting point. Do not add a password directly
to the YAML file. Keep credentials in an approved secret-management mechanism
or in the environment variable referenced by the configuration.

## 2. Validate configuration

```bash
red-govern config-validate
```

Validation checks configuration structure and values without requiring every
operational command to be executed.

## 3. Review effective non-secret settings

```bash
red-govern config-show
```

Review the selected profile, deployment mode, compatibility settings, output
locations, privacy controls, and read-only action settings. Credential values
should not be printed.

## 4. Run diagnostics

```bash
red-govern doctor
```

Diagnostics can check local dependencies, configuration, output locations, and
optionally Redshift connectivity.

## 5. Detect available capabilities

```bash
red-govern capabilities
```

Capability results help explain whether a system relation is available,
unavailable, restricted by permissions, or not relevant to the selected
deployment type.

## 6. Review command-specific help

```bash
red-govern inventory --help
red-govern quota --help
red-govern classify --help
red-govern queries --help
red-govern report --help
```

## 7. Run a focused assessment

A typical read-only sequence is:

```bash
red-govern privacy-audit
red-govern capabilities
red-govern inventory
red-govern quota
red-govern classify
red-govern queries
red-govern snapshot
red-govern changes
red-govern report
```

The correct sequence depends on the permissions, deployment type, and objective.
Start with a non-production environment or a tightly scoped reader identity.
Review [configuration](configuration.md), [permissions](permissions.md), and
[security](security.md) before processing production metadata.
