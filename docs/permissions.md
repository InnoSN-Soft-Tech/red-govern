# Permissions

Use a dedicated Redshift identity with the minimum permissions required for the
metadata and workload views used by the selected command.

## Least-privilege approach

A reader identity should normally be separated from administrator and
application identities. Grant only the metadata visibility required for the
assessment and review those grants through the organisation's normal access
process.

Avoid using administrator credentials merely to make capability checks pass.

## Detecting restricted access

Run:

```bash
red-govern doctor
red-govern capabilities
```

Capability detection distinguishes unavailable relations from permission
restrictions where Redshift exposes enough information to do so. A command may
return partial results when some relations are readable and others are not.

## Permissions vary by command

Inventory, query monitoring, classification, snapshots, and reports do not
necessarily require the same views. Review command-specific help before
requesting additional access:

```bash
red-govern inventory --help
red-govern queries --help
red-govern classify --help
```

## Read-only controls

The default action configuration is:

```yaml
actions:
  read_only: true
  allow_query_cancellation: false
  allow_database_writes: false
```

Keep these settings in place for normal governance assessments. A configuration
setting does not replace database-side least privilege; the connecting identity
must also be restricted appropriately.

## Troubleshooting access

When a capability is restricted:

1. record the command and sanitised error category;
2. confirm the deployment type;
3. identify the specific required system relation;
4. request only the narrow access needed;
5. rerun capability detection;
6. avoid sharing endpoints, account identifiers, usernames, or query text.

See [compatibility](compatibility.md) for deployment-aware behaviour and
[security](security.md) for credential handling.
