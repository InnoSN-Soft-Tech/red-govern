# Red-Govern Privacy Policy

Effective date: 7 August 2026

Red-Govern is a local-first Amazon Redshift governance project maintained by
InnoSN Soft Tech. This policy describes both the local Red-Govern package and
the planned public read-only metadata API.

## Local Red-Govern package

Configuration, snapshots, generated reports, and operational metadata remain on
the machine where the CLI runs unless the user deliberately moves or shares
them.

The starter configuration disables telemetry, external services, and query-text
capture. Red-Govern does not require users to send Redshift passwords, tokens,
private endpoints, connection strings, or unredacted production output to
InnoSN Soft Tech.

## Public remote metadata API

The remote metadata API runtime is implemented, but the production endpoint is
not deployed as of the effective date above. When deployed, the planned public
endpoint is:

```text
https://api.snsoft.tech/red-govern
```

The API is limited to public, versioned Red-Govern metadata: package version,
problem taxonomy, support status, the canonical command allowlist,
documentation links, and fixed safety boundaries.

The public metadata API:

- does not accept Redshift passwords, tokens, credentials, private endpoints, or
  connection strings;
- does not accept local Red-Govern configuration files or unredacted production
  outputs;
- does not connect to Amazon Redshift;
- does not execute SQL;
- does not execute Red-Govern commands;
- does not perform destructive remediation;
- does not prove that a database object is safe to delete;
- does not use application authentication or user accounts for this public
  metadata surface.

## Technical request metadata

A hosted HTTPS service necessarily processes limited technical information in
order to receive and protect requests. Depending on the selected hosting, DNS,
TLS, reverse-proxy, CDN, or security provider, this can include:

- source IP address;
- user agent and basic HTTP headers;
- request timestamp;
- requested route and query selector;
- response status and timing;
- network, abuse-prevention, and security events.

The Red-Govern application disables Uvicorn access logging in the recommended
deployment command. Infrastructure providers may still create operational or
security logs under their own service settings and policies. The deployment is
designed to minimize such logging and does not require application secrets.

Provider-specific disclosures and retention settings must be reviewed before
the production endpoint is activated.

## Cookies, advertising, and sale of data

The planned metadata API does not use cookies, advertising identifiers, or
behavioral advertising. InnoSN Soft Tech does not sell personal data collected
through the Red-Govern metadata API.

## Operational Redshift metadata

Local Red-Govern outputs can still reveal environment-specific identifiers,
database usernames, object names, query metadata, classification labels, local
paths, and report names. Review and redact operational outputs before sharing
them with any third party.

## Security and retention

The public metadata API is designed to expose only non-sensitive project
metadata and to accept no request body. Edge rate limiting, HTTPS, a non-root
container, restricted process permissions, and short network timeouts are part
of the deployment contract.

Any infrastructure log retention should be configured to the minimum period
needed for availability, abuse prevention, and security operations, subject to
the selected provider and applicable obligations.

## Changes to this policy

This policy may be updated as the hosting provider, deployment architecture, or
public API capabilities change. Material changes should be reflected in both
the repository copy and this public documentation page.

## Contact

Privacy questions about Red-Govern may be sent to `info@snsoft.tech`.
