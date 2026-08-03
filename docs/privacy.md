# Privacy

Red-Govern is designed for local-first operation. Configuration, snapshots, and
generated reports remain on the machine where the CLI runs unless the user
deliberately moves or shares them.

## Default privacy controls

The starter configuration disables telemetry, external services, and query-text
capture:

```yaml
privacy:
  telemetry: false
  capture_query_text: false
  redact_literals: true
  external_services: false
```

Query monitoring also defaults to query-text capture being disabled.

## Operational metadata can still be sensitive

Even without business-row data, governance outputs can reveal:

- account, cluster, or workgroup identifiers;
- database usernames;
- database, schema, table, and column names;
- query timing, frequency, status, and identifiers;
- classification labels;
- operational ownership or registry information;
- local paths and report names.

Treat reports and snapshots according to the data-handling requirements of the
organisation that owns the Redshift environment.

## Before sharing output

1. run `red-govern privacy-audit`;
2. review effective settings with `red-govern config-show`;
3. remove credentials, endpoints, account identifiers, and usernames;
4. redact confidential object names and query information;
5. confirm that the recipient is authorised;
6. use an approved transfer mechanism.

## Local storage

Keep generated JSON, Excel, and SQLite files outside shared folders and version
control. Restrictive local file permissions reduce accidental exposure but do
not replace endpoint security, disk encryption, access control, retention, or
secure deletion.

See [configuration](configuration.md) for privacy settings and
[security](security.md) for incident and vulnerability reporting.
