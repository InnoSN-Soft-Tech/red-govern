# Security

Red-Govern should be operated with a dedicated least-privilege identity, secure
credential handling, verified TLS, and read-only action controls.

## Credentials

Do not place passwords or tokens in configuration files, screenshots, issue
reports, example commands, shell scripts, or source control.

The default configuration reads the Redshift password from:

```text
RED_GOVERN_REDSHIFT_PASSWORD
```

Use an approved secret manager or protected environment injection where
available. Review shell-history and process-environment risks for the operating
system and execution environment.

## Transport security

TLS is enabled by default with certificate and hostname verification:

```yaml
redshift:
  ssl:
    enabled: true
    mode: verify-full
```

Do not weaken TLS validation to bypass an unresolved certificate or endpoint
problem.

## Safe operation

Before running against production:

```bash
red-govern config-validate
red-govern config-show
red-govern privacy-audit
red-govern doctor
red-govern capabilities
```

Keep database writes and query cancellation disabled unless a separately
reviewed feature explicitly requires them.

## Diagnostic redaction

Public issues and support requests must not contain credentials, private
endpoints, AWS account identifiers, cluster or workgroup identifiers, database
usernames, confidential object names, production query text, or personal data.

## Security reporting

Do not open a public issue for a vulnerability or suspected data exposure.
Follow the repository's
[security policy](https://github.com/InnoSN-Soft-Tech/red-govern/security/policy)
for the current private-reporting process.

For ordinary usage problems, use the
[support guide](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/SUPPORT.md).
