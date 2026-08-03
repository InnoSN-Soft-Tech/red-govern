# Red-Govern documentation

Red-Govern is a local-first command-line toolkit for Amazon Redshift governance
and operational intelligence. It helps engineers, analytics teams, platform
owners, and governance practitioners inspect Redshift environments without
building a custom governance utility from scratch.

!!! warning "Alpha software"

    The current release is `0.1.0a2`. Commands, configuration fields, report
    formats, and compatibility behaviour may change before the first stable
    release. Review command help before operating against a production
    environment.

## What Red-Govern covers

Red-Govern currently supports workflows for:

- capability discovery across Redshift system views;
- normalised database-object inventory;
- object-quota assessment;
- classification and operational-registry matching;
- privacy and safety auditing;
- query-workload inspection;
- local inventory snapshots and change comparison;
- local JSON, Excel, and command-line reporting.

## Start here

1. [Install Red-Govern](installation.md).
2. Follow the [quick start](quick-start.md).
3. Review the [configuration guide](configuration.md).
4. Confirm [Redshift compatibility](compatibility.md) and
   [permissions](permissions.md).
5. Read the [privacy](privacy.md), [security](security.md), and
   [limitations](limitations.md) guidance before using production metadata.

## Core principles

**Local-first operation:** configuration, snapshots, and generated reports stay
local unless the user deliberately moves or shares them.

**Credential-aware output:** effective-configuration and diagnostic workflows
are designed to avoid displaying credential values.

**Explicit validation:** configuration validation, environment diagnostics,
capability detection, tests, type checking, package validation, and continuous
integration are part of the project workflow.

**Incremental governance:** inventory, classification, quota analysis,
snapshotting, reporting, and workload inspection can be adopted separately.

Use `red-govern --help` and `red-govern <command> --help` as the authoritative
reference for the installed version.
