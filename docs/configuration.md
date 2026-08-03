# Configuration

Red-Govern uses a versioned YAML configuration. Create a starter file with:

```bash
red-govern init
```

Validate changes before running operational commands:

```bash
red-govern config-validate
red-govern config-show
```

## Main sections

The default configuration is organised into these sections:

| Section | Purpose |
|---|---|
| `redshift` | Connection, authentication, compatibility, and TLS settings |
| `governance` | Object quota, lifecycle, and query-monitoring behaviour |
| `classification` | Rules file and operational-registry configuration |
| `history` | Local snapshot backend, location, and retention |
| `outputs` | CLI, JSON, and Excel output controls |
| `privacy` | Telemetry, query-text, literal-redaction, and external-service controls |
| `actions` | Read-only and write-related safety controls |

## Safe connection example

```yaml
config_version: 1

redshift:
  profile_name: default

  connection:
    host: null
    port: 5439
    database: dev
    user: null
    connect_timeout_seconds: 15
    statement_timeout_seconds: 60
    tcp_keepalive: true

  authentication:
    method: auto
    password_env: RED_GOVERN_REDSHIFT_PASSWORD
    aws_profile: null
    cluster_identifier: null
    workgroup_name: null
    region: null
    db_user: null

  compatibility:
    mode: auto
    deployment_type: auto
    version_override: null
    prefer_sys_views: true
    allow_legacy_fallbacks: true

  ssl:
    enabled: true
    mode: verify-full
```

Set the password outside the file:

```bash
export RED_GOVERN_REDSHIFT_PASSWORD="replace-with-a-secret"
```

Do not paste a real password into shell history on shared systems. Use the
secret-management process approved for the environment.

## Safety-oriented defaults

The default configuration keeps telemetry and external services disabled,
disables query-text capture, enables literal redaction, and keeps database
actions read-only:

```yaml
privacy:
  telemetry: false
  capture_query_text: false
  redact_literals: true
  external_services: false

actions:
  read_only: true
  allow_query_cancellation: false
  allow_database_writes: false
```

## Local files

Classification rules, operational registries, snapshots, JSON reports, and
Excel reports can contain sensitive operational metadata. Keep them outside
version control, review file permissions, and redact them before sharing.

See [privacy](privacy.md), [security](security.md), and
[permissions](permissions.md) for the related controls.
