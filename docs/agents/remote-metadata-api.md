# Remote metadata API

Red-Govern `0.1.0a3` includes an optional read-only FastAPI runtime implementing
the frozen four-operation remote metadata contract:

```text
red_govern.remote_api:app
```

The Step 47.2E deployment assets are ready for hosting, but the production API is
still not deployed and Custom GPT Actions remain disabled.

The tracked Action-facing contracts are:

- [`remote-metadata-contract.json`](remote-metadata-contract.json)
- [`red-govern-metadata.openapi.json`](red-govern-metadata.openapi.json)

The API surface remains exactly:

| Operation | Purpose |
|---|---|
| `GET /v1/meta` | Return package version, platform, canonical counts, public links, and safety boundaries |
| `GET /v1/problems` | List canonical problem summaries, optionally filtered by support status |
| `GET /v1/problems/{problem_id}` | Return one canonical problem contract |
| `GET /v1/commands` | Return the canonical command allowlist as metadata |

The command endpoint does not execute Red-Govern commands.

## Deployment assets

The repository now includes:

- root [`Dockerfile`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/Dockerfile);
- root [`.dockerignore`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/.dockerignore);
- [`deployment/README.md`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/deployment/README.md);
- an example Nginx reverse-proxy contract in
  [`deployment/nginx-red-govern.conf.example`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/deployment/nginx-red-govern.conf.example).

The image runs as a non-root user on port `8080`, exposes `/v1/meta` as its
health endpoint, disables the Uvicorn access log and server header, and requires
no application secrets.

The planned public base URL remains:

```text
https://api.snsoft.tech/red-govern
```

The edge must strip the `/red-govern` prefix before forwarding requests to the
ASGI application.

## Public privacy policy

The public privacy policy is:

```text
https://innosn-soft-tech.github.io/red-govern/privacy/
```

`PRIVACY.md` and `docs/privacy.md` are validated as identical. The policy
covers both local-first behavior and the limited technical request metadata that
hosting infrastructure may process for a future public API.

## Runtime boundaries

The runtime accepts no request body and no application authentication secret.
Its only selectors are the optional problem `status` and canonical
`problem_id`.

It does not accept passwords, tokens, credentials, private endpoints,
connection strings, local Red-Govern configuration files, SQL, arbitrary
commands, or unredacted production outputs.

It does not connect to Amazon Redshift, execute SQL, execute Red-Govern
commands, write files, perform destructive remediation, or prove that an object
is safe to delete.

## Custom GPT status

**Custom GPT Actions remain disabled.** Current OpenAI GPT Actions require an
external API plus an OpenAPI schema, and public GPT Actions require a valid
Privacy Policy URL. The privacy URL is now prepared, but the production API and
DNS/TLS path must still be deployed and externally validated before Actions are
enabled.

The next phase is **Step 47.2F — hosting target selection and public API
deployment**.
