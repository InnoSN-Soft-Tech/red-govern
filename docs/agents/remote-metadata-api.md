# Remote metadata API

Red-Govern `0.1.0a3` includes an optional **read-only remote metadata API
runtime** implementing the frozen Step 47.2B contract. The runtime is implemented
in source as:

```text
red_govern.remote_api:app
```

The hosted endpoint at `https://api.snsoft.tech/red-govern` is **not deployed**
in Step 47.2C, and Custom GPT Actions remain disabled.

The tracked Action-facing contracts remain:

- [`remote-metadata-contract.json`](remote-metadata-contract.json)
- [`red-govern-metadata.openapi.json`](red-govern-metadata.openapi.json)

The runtime implements exactly four GET operations:

| Operation | Purpose |
|---|---|
| `GET /v1/meta` | Return package version, platform, canonical counts, public links, and safety boundaries |
| `GET /v1/problems` | List canonical problem summaries, optionally filtered by support status |
| `GET /v1/problems/{problem_id}` | Return one canonical problem contract |
| `GET /v1/commands` | Return the canonical command allowlist as metadata |

The command endpoint **does not execute Red-Govern commands**. It only returns
the version-matched allowlist from a packaged copy of the canonical problem map.
That packaged map is validated byte-for-byte against
`docs/problems/problem-command-map.json`.

## Source installation

Step 47.2C does not publish a new PyPI release. To test the optional runtime from
this source snapshot, use a separate or development environment:

```bash
python -m pip install --editable ".[remote]"
```

Start a local validation server bound only to loopback:

```bash
python -m uvicorn red_govern.remote_api:app \
  --host 127.0.0.1 \
  --port 8000
```

The FastAPI documentation, ReDoc, and generated OpenAPI routes are disabled in
the runtime. The version-controlled OpenAPI document above remains the
Action-facing schema.

## Runtime boundaries

The runtime accepts no request body and no authentication secret. Its only
request selectors are:

- optional `status` on `GET /v1/problems`;
- canonical `problem_id` on `GET /v1/problems/{problem_id}`.

It does not accept passwords, tokens, credentials, private endpoints,
connection strings, local Red-Govern configuration files, SQL, arbitrary
commands, or unredacted production outputs.

The runtime does not connect to Amazon Redshift, execute SQL, execute
Red-Govern commands, write files, perform destructive remediation, or prove
that an object is safe to delete.

The local configuration operations from Step 47.1 remain local and are **not**
remote-wrapped:

- `validate_config(path)`
- `get_redacted_config(path=<local file>)`
- `run_privacy_audit(path)`

## Custom GPT status

**Custom GPT Actions remain disabled.** Do not configure the planned Action
until the hosted endpoint and public privacy-policy URL are actually deployed
and pass separate external integration validation.

The next phase is **Step 47.2D — remote metadata API deployment readiness**.
