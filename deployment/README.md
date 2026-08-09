# Remote metadata API deployment assets

Step 47.2E adds provider-neutral deployment assets for the read-only
Red-Govern metadata API. These assets prepare the runtime for hosting; they do
**not** deploy a production service or enable Custom GPT Actions.

## Runtime contract

Container runtime:

```text
red_govern.remote_api:app
```

Container port:

```text
8080
```

Health endpoint inside the container:

```text
GET /v1/meta
```

Planned public base URL:

```text
https://api.snsoft.tech/red-govern
```

Planned public health URL:

```text
https://api.snsoft.tech/red-govern/v1/meta
```

The public reverse proxy must strip `/red-govern` before forwarding to the ASGI
application. For example, external `/red-govern/v1/meta` becomes upstream
`/v1/meta`.

## Container build

From the repository root:

```bash
docker build --tag red-govern-remote:0.1.0a4 .
```

Local container smoke test:

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --publish 127.0.0.1:8080:8080 \
  red-govern-remote:0.1.0a4
```

The image runs as the non-root `redgovern` user. The application server header
and Uvicorn access log are disabled. The runtime does not need credentials or
other secrets.

## Edge / reverse proxy

[`nginx-red-govern.conf.example`](nginx-red-govern.conf.example) documents the
required base-path rewrite, timeouts, response headers, request-size limit, and
rate limiting. TLS certificate paths are intentionally placeholders and no
certificate or private key belongs in this repository.

The edge should:

- terminate HTTPS for `api.snsoft.tech`;
- redirect plain HTTP to HTTPS;
- expose only `/red-govern/*`;
- strip `/red-govern` before proxying to `127.0.0.1:8080`;
- permit GET requests only for the metadata surface;
- apply reasonable per-client rate limiting;
- suppress upstream `Server` headers;
- keep request bodies small even though the application exposes no request body;
- avoid logging secrets because the API accepts none.

CORS is intentionally not enabled by the application. GPT Actions call the API
server-to-server and do not require browser CORS.

## Privacy

The public privacy-policy URL is:

```text
https://innosn-soft-tech.github.io/red-govern/privacy/
```

The repository root `PRIVACY.md` and `docs/privacy.md` are validated as identical
so the public policy surface does not drift from the source policy.

The policy explains that the application does not accept Redshift credentials
or local configuration, while normal hosting infrastructure may still process
technical request metadata such as IP address, user agent, timestamps, route,
status code, and security events.

## Not performed in Step 47.2E

This step does not create DNS records or perform any of the following actions:
- provision a hosting account or compute service;
- install TLS certificates;
- deploy the container;
- enable Custom GPT Actions;
- add Redshift connectivity;
- add SQL or command execution;
- publish a new PyPI release.

The next step selects the production hosting target and performs the public API
deployment plus external validation.
