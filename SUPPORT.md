# Support

Red-Govern is currently an alpha project. Support is provided on a
best-effort basis through the GitHub repository.

## Before requesting support

Confirm the installed version:

```bash
red-govern version
```

Review command help:

```bash
red-govern --help
red-govern <command> --help
```

Validate the configuration:

```bash
red-govern config-validate
```

Inspect the effective non-secret configuration:

```bash
red-govern config-show
```

Run diagnostics:

```bash
red-govern doctor
```

When relevant, also check Redshift feature availability:

```bash
red-govern capabilities
```

## Bug reports

Use a GitHub issue for reproducible defects that do not contain security or
sensitive-data concerns.

Include:

- Red-Govern version;
- Python version;
- operating system;
- installation method;
- command executed;
- expected behaviour;
- observed behaviour;
- relevant traceback or error output;
- whether the environment is provisioned Redshift or Redshift Serverless;
- whether the issue occurs without production data.

## Feature requests

Feature requests should explain:

- the governance or operational problem;
- the intended user;
- the proposed behaviour;
- expected inputs and outputs;
- Redshift compatibility considerations;
- privacy and security implications;
- possible alternatives.

## Sensitive information

Before sharing any diagnostic information, remove:

- passwords and tokens;
- Redshift endpoints;
- AWS account identifiers;
- cluster and workgroup identifiers;
- database usernames;
- internal database and schema names;
- table and column names where confidential;
- query text;
- customer, patient, employee, or other personal information;
- locally generated reports and snapshots unless carefully sanitised.

Never attach a real configuration file without reviewing and redacting it.

## Security issues

Do not use a public support issue for vulnerabilities or suspected data
exposure. Follow [SECURITY.md](SECURITY.md).

## Scope

Community support may cover:

- installation;
- CLI usage;
- configuration validation;
- Redshift capability compatibility;
- package and dependency issues;
- reproducible defects;
- documentation clarification.

The project does not provide emergency production support, managed Redshift
administration, incident response, or guarantees regarding a particular AWS
environment.
