# Remote metadata API contract

Red-Govern `0.1.0a3` now defines a **contract-only** read-only remote metadata
API intended for future Custom GPT Actions and other HTTP clients. Step 47.2B
defines the interface and OpenAPI schema only. The planned server is **not deployed**.

Planned server:

```text
https://api.snsoft.tech/red-govern
```

The contract is published in:

- [`remote-metadata-contract.json`](remote-metadata-contract.json)
- [`red-govern-metadata.openapi.json`](red-govern-metadata.openapi.json)

The OpenAPI document uses OpenAPI 3.1.0 and four GET-only operations:

| Operation | Purpose |
|---|---|
| `GET /v1/meta` | Return package version, platform, canonical counts, public links, and safety boundaries |
| `GET /v1/problems` | List canonical problem summaries, optionally filtered by support status |
| `GET /v1/problems/{problem_id}` | Return one canonical problem contract |
| `GET /v1/commands` | Return the canonical command allowlist as metadata |

The command endpoint **does not execute Red-Govern commands**. It only returns
the version-matched allowlist from the canonical problem map.

## Why the local 47.1 tools are not remote-wrapped

Three local typed operations depend wholly or partly on a file that exists on
the machine running Red-Govern:

- `validate_config(path)`
- `get_redacted_config(path=<local file>)`
- `run_privacy_audit(path)`

A hosted service cannot read a caller's local path. Step 47.2B therefore does
not accept uploaded configuration, credentials, private endpoints, connection
strings, or unredacted production output to imitate those local semantics.

The remote metadata contract does not connect to Amazon Redshift, execute SQL,
write files, run arbitrary commands, perform destructive remediation, or prove
that an object is safe to delete.

## Authentication and privacy

The proposed metadata is already public in versioned Red-Govern documentation,
so the contract uses no authentication. That is a contract decision, not a
statement that a server is currently available.

`PRIVACY.md` is the source privacy notice for this future public metadata
surface. A deployed Action still needs a reachable API and a valid privacy
policy URL before public GPT sharing.

## Custom GPT status

**Custom GPT Actions remain disabled** in Step 47.2B. Do not paste this schema
into a production GPT Action until the planned server and privacy-policy URL are
actually live and the runtime passes its own integration validation.

The next implementation phase is **Step 47.2C**: build the remote metadata API
runtime against this frozen contract without adding Redshift connectivity,
credential intake, SQL execution, or local-configuration upload.
