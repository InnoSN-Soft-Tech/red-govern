# Red-Govern Privacy Notice

Red-Govern is local-first. The current `0.1.0a3` package is designed so that
configuration, snapshots, and generated reports remain on the machine where the
CLI runs unless the user deliberately moves or shares them.

## Current package behavior

The current package does not operate a hosted Red-Govern service. Telemetry and
external services are disabled by default in the starter configuration. Users
remain responsible for handling generated operational metadata according to
their organisation's policies.

## Remote metadata contract

The Step 47.2B remote metadata API contract is not deployed. It defines a future
read-only HTTP surface for public, versioned package metadata such as the
Red-Govern version, problem taxonomy, support status, canonical command
allowlist, documentation links, and safety boundaries.

That future public metadata surface:

- does not accept passwords, tokens, credentials, private endpoints, connection
  strings, or unredacted production outputs;
- does not accept local Red-Govern configuration files;
- does not connect to Amazon Redshift;
- does not execute SQL;
- does not execute Red-Govern commands;
- does not provide destructive remediation or prove that an object is safe to
  delete.

The planned metadata contract uses only information already published in the
Red-Govern repository and documentation. No Action endpoint is live in Step
47.2B, and Custom GPT Actions remain disabled until a deployed runtime and
public privacy-policy URL pass separate validation.

## Operational data

Even local governance metadata can reveal environment-specific identifiers,
database usernames, object names, query metadata, classification labels, local
paths, and report names. Review and redact operational outputs before sharing
them.

## Contact

Privacy questions about Red-Govern may be sent to `info@snsoft.tech`.
