# Security Policy

Security and privacy are core concerns for Red-Govern because the project may
interact with database metadata, operational history, query information, account
configuration, and locally stored reports.

## Supported versions

Red-Govern is currently an alpha project.

| Version | Security support |
|---|---|
| `0.1.x` | Current alpha line |
| Earlier versions | Not supported |

Users should upgrade to the latest available release before reporting behaviour
that may already have been corrected.

## Reporting a vulnerability

Do not report suspected vulnerabilities through a public GitHub issue.

Use the repository's **Security** tab and submit a private vulnerability report
when that option is available. Otherwise, contact the InnoSN Soft Tech
repository maintainers privately through an appropriate GitHub channel.

Include:

- the affected Red-Govern version;
- the operating system and Python version;
- the affected command or module;
- reproduction steps;
- expected and observed behaviour;
- potential impact;
- whether credentials, Redshift metadata, reports, or query information could
  be exposed;
- a proposed fix, when available.

Do not include live passwords, tokens, private keys, connection strings, or
unredacted production data.

## Sensitive areas

Reports are especially important when they involve:

- credential exposure;
- unsafe configuration display;
- logging of sensitive values;
- command injection;
- path traversal;
- unsafe file permissions;
- report or snapshot data leakage;
- dependency compromise;
- GitHub Actions permission escalation;
- PyPI publishing identity or supply-chain compromise;
- unintended Redshift mutations;
- bypass of configured privacy or safety controls.

## Coordinated disclosure

Please allow maintainers a reasonable opportunity to investigate and prepare a
fix before publicly disclosing a vulnerability.

Maintainers will aim to:

1. acknowledge the report;
2. assess impact and reproducibility;
3. develop and validate a correction;
4. publish an appropriate release or mitigation;
5. credit the reporter when requested and appropriate.

Exact timelines depend on severity, reproducibility, and maintainer
availability.

## Credential handling

Red-Govern users should:

- use a dedicated Redshift identity;
- grant only the permissions needed for the intended analysis;
- keep credentials outside version control;
- use approved secret-management mechanisms;
- rotate credentials that may have been exposed;
- redact screenshots, logs, reports, snapshots, and issue attachments;
- review `red-govern config-show` and `red-govern privacy-audit` output before
  sharing diagnostics.

## Release security

Official PyPI publishing is performed through GitHub Actions OIDC Trusted
Publishing. Permanent PyPI passwords and API tokens should not be added to the
repository or GitHub environment.
