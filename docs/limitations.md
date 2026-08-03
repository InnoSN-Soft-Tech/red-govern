# Limitations

Red-Govern is alpha software. The current release is suitable for controlled
evaluation and carefully reviewed governance workflows, not for assuming
complete coverage of every Redshift environment.

## Current limitations

- Redshift system-view availability differs between provisioned and Serverless
  deployments.
- Permissions can produce partial capability and inventory results.
- Service changes can alter system-view columns or behaviour.
- Classification quality depends on the configured rules and operational
  registry.
- Quota interpretation depends on the confirmed limit for the environment.
- Query analysis can be intentionally limited when query-text capture is
  disabled.
- Local reports and snapshots require the user to apply appropriate retention
  and handling controls.
- Report formats and command options may change before the stable release.

## What Red-Govern does not provide

Red-Govern does not provide emergency production support, managed Redshift
administration, incident response, a guarantee of complete metadata visibility,
or a substitute for AWS account governance and database-side access control.

## Interpreting incomplete results

An empty or partial result does not always mean that no matching activity
exists. Confirm:

1. the deployment type;
2. capability-detection results;
3. the permissions of the connecting identity;
4. the command's time range and filters;
5. the compatibility settings;
6. whether required optional inputs are configured.

Use `red-govern doctor`, `red-govern capabilities`, and command-specific help
before reporting a defect.

Review [compatibility](compatibility.md), [permissions](permissions.md), and
[privacy](privacy.md) alongside these limitations.
